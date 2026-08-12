FROM llmquest-sandbox:latest

USER root

# Allow deployments to select a nearby, reliable PyPI mirror.  The extra
# timeout/retry settings are important for the large CPU PyTorch wheel.
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=5

# ML lessons use a separate image so ordinary programming lessons do not pay
# the PyTorch/Transformers download and memory cost. Keep model weights out of
# the image: each lesson must use a reviewed small fixture or cached artifact.
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} \
    torch \
    transformers \
    peft \
    sentence-transformers

USER runner
WORKDIR /home/runner
