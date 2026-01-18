COPY requirements.txt pyproject.toml ./
RUN pip3 install --no-cache-dir --upgrade pip setuptools>=64 wheel

# Adding PyTorch with CUDA support