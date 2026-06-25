"""Modal serverless GPU function running dots.mocr inference.

This is Docflow's production GPU boundary (Phase 1): page images in, layout JSON out,
and nothing else. The local engine's ``ModalDotsModel`` calls ``DotsOCR.parse.remote(pages)``.

Because Modal gives us an L4 (Ada, sm_89), flash-attn works here — so this runs the official
dots.mocr config (flash_attention_2, full resolution, max_new_tokens=24000) with none of the
T4 workarounds the Colab notebook needs.

    Deploy:  uv run modal deploy modal_app.py
    Smoke:   uv run modal run modal_app.py::smoke
"""

from __future__ import annotations

import io
import json
import math
import re

import modal

MODEL_REPO = "rednote-hilab/dots.mocr"
# The repo id contains a '.', which breaks transformers' trust_remote_code dynamic
# import. A dot-free directory sidesteps it (same fix as Phase 0).
WEIGHTS_DIR = "/weights/DotsMOCR"

# --- Inference tuning -------------------------------------------------------------
MAX_PIXELS = 4_000_000   # L4 has 24 GB; effectively full-page resolution
MIN_PIXELS = 200_000
MAX_NEW_TOKENS = 24000   # official dots.mocr default
FACTOR = 28              # vision patch(14) x 2x2 merge -> dims must be multiples of 28

# Exact official dots.mocr layout prompt (dots_mocr.utils.dict_promptmode_to_prompt).
PROMPT = """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]

2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].

3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown. Preserve the visual hierarchy of the page: give titles and section or sub-section headings the matching Markdown heading level (#, ##, ###, ...) according to how prominent they appear, and use **bold** or *italic* to reflect emphasized labels and inline emphasis. Keep list items in Markdown list syntax.

4. Constraints:
    - The output text must be the original text from the image, with no translation.
    - All layout elements must be sorted according to human reading order.

5. Final Output: The entire output must be a single JSON object.
"""

app = modal.App("docflow-ocr")
weights = modal.Volume.from_name("docflow-weights", create_if_missing=True)


def _download_weights() -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(MODEL_REPO, local_dir=WEIGHTS_DIR)


# CUDA-devel base so flash-attn can build from source (cached after the first deploy).
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.12")
    .pip_install("torch==2.7.0")
    .pip_install(
        "transformers==4.57.6",
        "qwen-vl-utils",
        "accelerate",
        "huggingface_hub",
        "pillow",
    )
    .pip_install("flash-attn==2.8.0.post2", extra_options="--no-build-isolation")
    .run_function(_download_weights, volumes={"/weights": weights})
)

# Heavy libs import only inside the container, not on the local machine running `modal deploy`.
with image.imports():
    import torch
    from PIL import Image
    from qwen_vl_utils import process_vision_info
    from transformers import AutoModelForCausalLM, AutoProcessor


def _smart_resize(w: int, h: int) -> tuple[int, int]:
    """Round to multiples of FACTOR, keeping aspect, within [MIN_PIXELS, MAX_PIXELS]."""
    w_bar = max(FACTOR, round(w / FACTOR) * FACTOR)
    h_bar = max(FACTOR, round(h / FACTOR) * FACTOR)
    if w_bar * h_bar > MAX_PIXELS:
        beta = math.sqrt((w * h) / MAX_PIXELS)
        w_bar = max(FACTOR, math.floor(w / beta / FACTOR) * FACTOR)
        h_bar = max(FACTOR, math.floor(h / beta / FACTOR) * FACTOR)
    elif w_bar * h_bar < MIN_PIXELS:
        beta = math.sqrt(MIN_PIXELS / (w * h))
        w_bar = math.ceil(w * beta / FACTOR) * FACTOR
        h_bar = math.ceil(h * beta / FACTOR) * FACTOR
    return w_bar, h_bar


def _to_elements(text: str):
    """Parse the model's decoded text into a list of element dicts.
    Tolerates code fences and either a JSON array or a {"elements": [...]} object."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if not m:
            raise ValueError(f"No JSON found in model output: {text[:500]!r}")
        data = json.loads(m.group(0))
    if isinstance(data, dict):
        for key in ("elements", "layout", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return data


@app.cls(gpu="L4", image=image, volumes={"/weights": weights}, scaledown_window=300)
class DotsOCR:
    @modal.enter()
    def load(self) -> None:
        self.model = AutoModelForCausalLM.from_pretrained(
            WEIGHTS_DIR,
            attn_implementation="flash_attention_2",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        self.processor = AutoProcessor.from_pretrained(WEIGHTS_DIR, trust_remote_code=True)
        if hasattr(self.processor, "image_processor"):
            self.processor.image_processor.max_pixels = MAX_PIXELS
            self.processor.image_processor.min_pixels = MIN_PIXELS

    def _parse_image(self, image):
        w0, h0 = image.size
        w1, h1 = _smart_resize(w0, h0)
        small = image.resize((w1, h1)) if (w1, h1) != (w0, h0) else image

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": small},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ]
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt",
        ).to(self.model.device)
        inputs.pop("mm_token_type_ids", None)  # processor emits it; generate() rejects it

        with torch.inference_mode():
            generated = self.model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated)]
        decoded = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]
        elements = _to_elements(decoded)

        # Scale bboxes from the resized space back to the original image pixels so the
        # local engine's figure cropping (which assumes original render dims) lines up.
        sx, sy = w0 / w1, h0 / h1
        for e in elements:
            if isinstance(e, dict) and e.get("bbox"):
                x1, y1, x2, y2 = e["bbox"]
                e["bbox"] = [x1 * sx, y1 * sy, x2 * sx, y2 * sy]
        return elements

    @modal.method()
    def parse(self, pages: list[dict]) -> list[dict]:
        """pages: [{"page_index": int, "png": bytes}] -> list of PageLayout dicts."""
        out: list[dict] = []
        for p in pages:
            image = Image.open(io.BytesIO(p["png"])).convert("RGB")
            elements = self._parse_image(image)
            out.append(
                {
                    "page_index": p["page_index"],
                    "image_width": image.width,
                    "image_height": image.height,
                    "elements": [
                        {"category": e.get("category"), "bbox": e.get("bbox"), "text": e.get("text")}
                        for e in elements
                        if isinstance(e, dict)
                    ],
                }
            )
        return out


@app.local_entrypoint()
def smoke() -> None:
    """Send one blank page through the deployed function: `modal run modal_app.py::smoke`."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", (1000, 1400), "white").save(buf, format="PNG")
    pages = [{"page_index": 0, "png": buf.getvalue()}]
    result = DotsOCR().parse.remote(pages)
    print("pages:", len(result), "| elements on page 0:", len(result[0]["elements"]))
    print(result[0])
