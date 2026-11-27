"""Run an interactive local Hebrew chat using an IvritLM checkpoint."""
import argparse
from pathlib import Path

import torch

from ivritlm.config import ModelConfig
from ivritlm.model import IvritLM
from ivritlm.tokenizer import ByteTokenizer, EOS_ID


def generate_reply(model, tokenizer, history, device, max_new_tokens, temperature):
    prompt = "".join(f"### {role}\n{text.strip()}\n" for role, text in history) + "### assistant\n"
    encoded = [tokenizer.bos_id, *tokenizer.encode(prompt, add_special_tokens=False)]
    context = torch.tensor([encoded], dtype=torch.long, device=device)
    generated = []
    model.eval()
    with torch.no_grad():
        for _ in range(max_new_tokens):
            cropped = context[:, -model.config.context_length:]
            logits, _ = model(cropped)
            next_logits = logits[:, -1, :] / max(temperature, 0.05)
            next_id = torch.multinomial(torch.softmax(next_logits, dim=-1), 1)
            token_id = int(next_id.item())
            if token_id == EOS_ID:
                break
            generated.append(token_id)
            context = torch.cat([context, next_id], dim=1)
            decoded = tokenizer.decode(generated)
            if "\n### user" in decoded or "\n### system" in decoded:
                decoded = decoded.split("\n### ", 1)[0]
                break
    return tokenizer.decode(generated).split("\n### user", 1)[0].split("\n### system", 1)[0].strip()


def main():
    parser = argparse.ArgumentParser(description="Interactive local chat with IvritLM.")
    parser.add_argument("--checkpoint", default="artifacts/pretraining/checkpoint.pt")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")
    path = Path(args.checkpoint)
    if not path.is_file():
        raise SystemExit(f"Checkpoint not found: {path}")
    state = torch.load(path, map_location="cpu", weights_only=False)
    config = ModelConfig(**state["model_config"])
    model = IvritLM(config)
    model.load_state_dict(state["model_state_dict"])
    model.to(args.device)
    tokenizer = ByteTokenizer()
    history = []
    print("IvritLM local chat. כתוב /exit לסיום, /reset לאיפוס השיחה.")
    while True:
        try:
            user_text = input("\nאתה: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nלהתראות.")
            break
        if not user_text:
            continue
        if user_text.lower() in {"/exit", "/quit"}:
            print("להתראות.")
            break
        if user_text.lower() == "/reset":
            history.clear()
            print("השיחה אופסה.")
            continue
        history.append(("user", user_text))
        # Keep the prompt within the model's short context window.
        while len(history) > 2:
            prompt = "".join(f"### {role}\n{text}\n" for role, text in history) + "### assistant\n"
            if len(prompt.encode("utf-8")) <= config.context_length - 16:
                break
            history.pop(0)
        answer = generate_reply(model, tokenizer, history, args.device,
                                args.max_new_tokens, args.temperature)
        if not answer:
            answer = "לא הצלחתי ליצור תשובה. כדאי לאמן עוד על דוגמאות שיחה."
        print("\nIvritLM: " + answer)
        history.append(("assistant", answer))


if __name__ == "__main__":
    main()
