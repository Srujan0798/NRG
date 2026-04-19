# Dockerfile for llama.cpp server
FROM ghcr.io/ggerganov/llama.cpp:server

# Model configuration
ENV MODEL=/models/llama-3.1-8b.Q4_K_M.gguf
ENV N_CTX=8192
ENV N_GPU_LAYERS=35

# Download model script
RUN mkdir -p /models

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["/server"]
CMD ["-m", "/models/llama-3.1-8b.Q4_K_M.gguf", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "-c", "8192", \
     "-n", "1024"]
