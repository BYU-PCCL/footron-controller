#!/usr/bin/python3

import sys

import torch

if __name__ == "__main__":
    try:
        torch.Tensor([1]).to("cuda")
        sys.exit(0)
    except RuntimeError:
        sys.exit(1)
