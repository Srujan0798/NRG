#!/usr/bin/env python3
"""
Text Chunking Pipeline for NRG 600GB Dataset
Creates overlapping chunks for embedding processing
"""

import argparse
import logging
import sys
import os
import re
from pathlib import Path
from typing import List, Iterator


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("chunking.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_arguments():
    parser = argparse.ArgumentParser(description="Chunk text fields for embedding")
    parser.add_argument("--source", required=True, help="Source data directory or file")
    parser.add_argument("--output", required=True, help="Output directory for chunks")
    parser.add_argument(
        "--chunk-size", type=int, default=512, help="Chunk size in tokens"
    )
    parser.add_argument(
        "--overlap", type=int, default=64, help="Overlap size in tokens"
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        default=["abstract", "bio", "description"],
        help="Text fields to chunk",
    )
    return parser.parse_args()


def simple_tokenize(text: str) -> List[str]:
    """Simple tokenization by splitting on whitespace and punctuation"""
    # Remove extra whitespace and split
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens


def detokenize(tokens: List[str]) -> str:
    """Convert tokens back to text"""
    return " ".join(tokens)


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into overlapping chunks

    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in tokens
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    tokens = simple_tokenize(text)

    if len(tokens) <= chunk_size:
        return [detokenize(tokens)]

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(detokenize(chunk_tokens))

        if end >= len(tokens):
            break

        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def process_file(
    file_path: Path, output_dir: Path, chunk_size: int, overlap: int, fields: List[str]
) -> int:
    """
    Process a single file and extract chunks from specified fields

    Args:
        file_path: Path to input file
        output_dir: Directory to write chunks
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        fields: List of field names to process

    Returns:
        Number of chunks created
    """
    # Placeholder implementation - would parse actual data format
    logging.info(f"Processing file: {file_path}")

    # Simulate processing
    chunks_created = 0

    # In real implementation, this would:
    # 1. Load the file (JSON, CSV, etc.)
    # 2. Extract text from specified fields
    # 3. Apply chunking to each field
    # 4. Write chunks to output with metadata

    # For now, create dummy chunks
    sample_texts = [
        "This is a sample abstract about machine learning research in artificial intelligence.",
        "Researcher biography focusing on neural networks and deep learning applications.",
        "Project description detailing climate modeling and environmental impact studies.",
    ]

    for i, text in enumerate(sample_texts):
        chunks = chunk_text(text, chunk_size, overlap)
        for j, chunk in enumerate(chunks):
            chunk_file = output_dir / f"{file_path.stem}_field_{i}_chunk_{j}.txt"
            chunk_file.write_text(chunk)
            chunks_created += 1

    return chunks_created


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_arguments()

    logger.info("Starting text chunking pipeline")
    logger.info(f"Source: {args.source}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Chunk size: {args.chunk_size}")
    logger.info(f"Overlap: {args.overlap}")
    logger.info(f"Fields: {args.fields}")

    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Process source
    source_path = Path(args.source)
    total_chunks = 0

    if source_path.is_file():
        total_chunks = process_file(
            source_path, output_path, args.chunk_size, args.overlap, args.fields
        )
    elif source_path.is_dir():
        # Process all files in directory
        for file_path in source_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                chunks = process_file(
                    file_path, output_path, args.chunk_size, args.overlap, args.fields
                )
                total_chunks += chunks
                logger.info(f"Processed {file_path.name}: {chunks} chunks")
    else:
        logger.error(f"Source path does not exist: {args.source}")
        sys.exit(1)

    logger.info(f"Chunking completed. Total chunks created: {total_chunks}")


if __name__ == "__main__":
    main()
