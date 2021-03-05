# SkeletonGraph

## install conda environment
```conda env create -f environment.yml```

## run.py parameters
```
python run.py -h
usage: run.py [-h] -i INPUT [-d] [-o OUTPUT]

Skeleton Graph Example

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to input image
  -d, --display         Display output (default: False)
  -o OUTPUT, --output OUTPUT
                        Path to output file
```

## example run
### command:
```python run.py -i example_images/JDoe1.png -d -o example_output/JDoe1.png.gxl```

### output gxl-file (-o, --output)
[example_output/JDoe1.png.gxl](example_output/JDoe1.png.gxl)

### output display (-d, --display)
![example_output/JDoe1.png.display.png](example_output/JDoe1.png.display.png)
