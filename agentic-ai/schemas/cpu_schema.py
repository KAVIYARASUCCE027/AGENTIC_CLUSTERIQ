"""
CPU Schema Module.

Defines Pydantic models for CPU-related API request and response payloads.
Provides strict validation and serialization for the /cpu endpoint.
"""

from pydantic import BaseModel, Field


class CPURequest(BaseModel):
    """
    Request model for CPU analysis endpoint.

    Attributes:
        namespace: The Kubernetes namespace containing the target pod.
        pod_name: The name of the pod to analyze CPU usage for.
    """

    namespace: str = Field(
        ...,
        min_length=1,
        max_length=253,
        description="The Kubernetes namespace containing the target pod.",
        examples=["default"],
    )
    pod_name: str = Field(
        ...,
        min_length=1,
        max_length=253,
        description="The name of the pod to analyze CPU usage for.",
        examples=["nginx"],
    )


class CPUResponse(BaseModel):
    """
    Response model for CPU analysis endpoint.

    Attributes:
        status: The status of the analysis (e.g., 'success', 'error').
        message: A detailed message containing the analysis result
                 or error description.
    """

    status: str = Field(
        ...,
        description="The status of the analysis operation.",
        examples=["success"],
    )
    message: str = Field(
        ...,
        description="Detailed analysis result or error description.",
        examples=["CPU usage is within normal limits at 75%."],
    )
