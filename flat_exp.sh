#!/bin/bash

niter=60000

# python main.py --exp flatinput --trajlen 2 --use_gpu --device 2 --niters 2000 --batch_size 256 1> log.txt 2> err.txt

# python main.py --exp flatinput --trajlen 2 --use_gpu --device 2 --niters 2000 --batch_size 128 --num_workers 2 --debug --override_data --override_model

python main.py --exp flatinput --trajlen 2 --use_gpu --device 3 --niters $niter --batch_size 128 --num_workers 2