from dataclasses import dataclass, field

@dataclass
class GradioArguments:
    """
    Gradio interface arguments
    """
    gradio_host: str = field(
        default="0.0.0.0",
        metadata={"help": "Gradio interface host"}
    )
    gradio_port: int = field(
        default=7860,
        metadata={"help": "Gradio interface port"}
    ) 