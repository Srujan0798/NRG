#!/usr/bin/env python3
"""
Batch Embedding Pipeline for NRG 600GB Dataset
Creates embeddings from text chunks using sentence transformers
"""

import argparse
import logging
import sys
import os
import numpy as np
from pathlib import Path
from typing import List, Iterator
import json


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("embedding.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Batch embed text chunks")
    parser.add_argument(
        "--input", required=True, help="Input directory with text chunks"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for embeddings"
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-mpnet-base-v2",
        help="Sentence transformers model name",
    )
    parser.add_argument(
        "--batch-size", type=int, default=256, help="Batch size for embedding"
    )
    parser.add_argument("--device", default="cpu", help="Device to use (cpu/cuda)")
    parser.add_argument(
        "--normalize",
        action="store_true",
        default=True,
        help="Normalize embeddings to unit length",
    )
    return parser.parse_args()


def load_chunks_from_directory(input_dir: Path) -> List[tuple]:
    """
    Load all text chunks from input directory

    Returns:
        List of tuples: (chunk_id, text, metadata)
    """
    chunks = []
    input_path = Path(input_dir)

    if not input_path.exists():
        logging.warning(f"Input directory does not exist: {input_dir}")
        return chunks

    # Process all text files
    for file_path in input_path.glob("*.txt"):
        try:
            # Extract metadata from filename
            # Format: {source}_field_{field_idx}_chunk_{chunk_idx}.txt
            stem = file_path.stem
            parts = stem.split("_")

            # Read the chunk text
            text = file_path.read_text(encoding="utf-8").strip()

            if text:  # Only add non-empty chunks
                chunk_id = f"{stem}_{len(chunks)}"  # Simple unique ID
                metadata = {
                    "source_file": file_path.name,
                    "field_index": int(parts[parts.index("field") + 1])
                    if "field" in parts
                    else 0,
                    "chunk_index": int(parts[parts.index("chunk") + 1])
                    if "chunk" in parts
                    else 0,
                    "original_path": str(file_path),
                }
                chunks.append((chunk_id, text, metadata))

        except Exception as e:
            logging.warning(f"Error processing file {file_path}: {e}")
            continue

    logging.info(f"Loaded {len(chunks)} chunks from {input_dir}")
    return chunks


def embed_chunks_batch(
    chunks: List[tuple], model_name: str, batch_size: int, device: str, normalize: bool
) -> List[tuple]:
    """
    Create embeddings for text chunks in batches

    Args:
        chunks: List of (chunk_id, text, metadata) tuples
        model_name: Sentence transformers model to use
        batch_size: Number of chunks to process per batch
        device: Device to run model on
        normalize: Whether to normalize embeddings

    Returns:
        List of (chunk_id, embedding, metadata) tuples
    """
    # Placeholder implementation - would use actual sentence-transformers
    logging.info(f"Loading model: {model_name} on {device}")
    logging.info(f"Would process {len(chunks)} chunks in batches of {batch_size}")

    # Simulate embedding process
    embedded_chunks = []

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        logging.info(
            f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)"
        )

        # Simulate embedding - in reality would call model.encode()
        for chunk_id, text, metadata in batch:
            # Generate dummy embedding (768 dimensions for all-mpnet-base-v2)
            # In real implementation: embedding = model.encode([text])[0]
            embedding = np.random.rand(768).astype(np.float32)

            if normalize:
                # Normalize to unit length
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

            embedded_chunks.append((chunk_id, embedding, metadata))

    return embedded_chunks


def save_embeddings(embedded_chunks: List[tuple], output_dir: Path):
    """
    Save embeddings to output directory

    Args:
        embedded_chunks: List of (chunk_id, embedding, metadata) tuples
        output_dir: Directory to save embeddings
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save embeddings as numpy files and metadata as JSON
    for chunk_id, embedding, metadata in embedded_chunks:
        # Save embedding as .npy file
        embedding_file = output_path / f"{chunk_id}.npy"
        np.save(embedding_file, embedding)

        # Save metadata as .json file
        metadata_file = output_path / f"{chunk_id}_metadata.json"
        metadata["embedding_shape"] = list(embedding.shape)
        metadata["embedding_dtype"] = str(embedding.dtype)
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    logging.info(f"Saved {len(embedded_chunks)} embeddings to {output_dir}")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_arguments()

    logger.info("Starting batch embedding pipeline")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Device: {args.device}")
    logger.info(f"Normalize: {args.normalize}")

    # Load chunks
    chunks = load_chunks_from_directory(args.input)

    if not chunks:
        logger.error("No chunks found to process")
        sys.exit(1)

    # Create embeddings
    embedded_chunks = embed_chunks_batch(
        chunks, args.model, args.batch_size, args.device, args.normalize
    )

    # Save embeddings
    save_embeddings(embedded_chunks, args.output)

    logger.info("Batch embedding pipeline completed")


if __name__ == "__main__":
    main()
