from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 258
    context_length: int = 256
    d_model: int = 256
    n_heads: int = 4
    n_layers: int = 4
    dropout: float = 0.1

    def validate(self):
        if self.vocab_size != 258:
            raise ValueError("Initial UTF-8 byte tokenizer requires vocab_size=258.")
        if self.context_length < 8 or self.d_model < 32:
            raise ValueError("context_length must be >= 8 and d_model >= 32.")
        if self.n_heads < 1 or self.d_model % self.n_heads:
            raise ValueError("d_model must be divisible by n_heads.")
        if self.n_layers < 1 or not 0 <= self.dropout < 1:
            raise ValueError("n_layers must be positive and dropout in [0, 1).")

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class TrainConfig:
    steps: int = 100
    batch_size: int = 8
    learning_rate: float = 3e-4
    seed: int = 42
    validation_fraction: float = 0.05
    log_interval: int = 10

    def validate(self):
        if not 1 <= self.steps <= 100000:
            raise ValueError("steps must be between 1 and 100000.")
        if not 1 <= self.batch_size <= 128:
            raise ValueError("batch_size must be between 1 and 128.")
        if not 0 < self.learning_rate <= 0.01:
            raise ValueError("learning_rate must be in (0, 0.01].")
        if not 0 < self.validation_fraction < 0.5:
            raise ValueError("validation_fraction must be in (0, 0.5).")
