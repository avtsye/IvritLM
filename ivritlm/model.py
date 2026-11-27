import torch
from torch import nn
from torch.nn import functional as F
from .config import ModelConfig

class TransformerBlock(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.d_model)
        self.attn = nn.MultiheadAttention(config.d_model, config.n_heads, dropout=config.dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(config.d_model)
        self.mlp = nn.Sequential(nn.Linear(config.d_model, 4 * config.d_model), nn.GELU(), nn.Linear(4 * config.d_model, config.d_model), nn.Dropout(config.dropout))

    def forward(self, x):
        length = x.size(1)
        mask = torch.triu(torch.ones(length, length, device=x.device, dtype=torch.bool), diagonal=1)
        normalized = self.norm1(x)
        attended, _ = self.attn(normalized, normalized, normalized, attn_mask=mask, need_weights=False)
        x = x + attended
        return x + self.mlp(self.norm2(x))

class IvritLM(nn.Module):
    """Decoder-only Transformer with randomly initialized weights."""
    def __init__(self, config=None):
        super().__init__()
        self.config = config or ModelConfig()
        self.config.validate()
        self.token_embedding = nn.Embedding(self.config.vocab_size, self.config.d_model)
        self.position_embedding = nn.Embedding(self.config.context_length, self.config.d_model)
        self.blocks = nn.Sequential(*(TransformerBlock(self.config) for _ in range(self.config.n_layers)))
        self.final_norm = nn.LayerNorm(self.config.d_model)
        self.lm_head = nn.Linear(self.config.d_model, self.config.vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight
        self.apply(self._init_weights)

    @staticmethod
    def _init_weights(module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, input_ids, targets=None):
        _, length = input_ids.shape
        if length > self.config.context_length:
            raise ValueError("Input exceeds configured context_length.")
        positions = torch.arange(length, device=input_ids.device)
        x = self.token_embedding(input_ids) + self.position_embedding(positions)[None, :, :]
        x = self.blocks(x)
        logits = self.lm_head(self.final_norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, input_ids, max_new_tokens=100, temperature=1.0):
        if temperature <= 0:
            raise ValueError("temperature must be positive.")
        self.eval()
        for _ in range(max_new_tokens):
            context = input_ids[:, -self.config.context_length:]
            logits, _ = self(context)
            next_id = torch.multinomial(torch.softmax(logits[:, -1, :] / temperature, dim=-1), 1)
            input_ids = torch.cat((input_ids, next_id), dim=1)
        return input_ids
