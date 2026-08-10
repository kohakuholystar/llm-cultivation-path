FROM python:3.12-slim

# 构建期 pip 源(默认官方; 境内服务器构建传 --build-arg PIP_INDEX_URL=https://mirrors.tencentyun.com/pypi/simple)
ARG PIP_INDEX_URL=https://pypi.org/simple

# 预装学习者可能用到的库(不含 torch, 太大; 需要时学习者代码可 pip install)
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} \
    openai>=1.0 \
    langchain>=0.1 \
    langchain-community \
    langchain-openai \
    chromadb \
    faiss-cpu \
    pydantic \
    requests \
    beautifulsoup4 \
    lxml \
    python-dotenv \
    pytest \
    numpy \
    pandas \
    tiktoken

# 非 root 用户
RUN useradd -m runner
USER runner
WORKDIR /home/runner

# 容器通过 stdin 接收代码: docker run -i ... python -c "import sys; exec(sys.stdin.read())"
