# tapIOca

Tools for transforming output files from
[Mandyoc](https://bitbucket.org/victorsacek/mandyoc/src/master/) code to dataset

## How to install

First clone the repository and navigate through the newly created directory.

### Dependencies

The package needs the following dependencies to run:

- `numpy`
- `scipy`
- `xarray`
- `matplotlib`


If you have an Anaconda Python distribution, you could install all the dependencies
through the `conda` package manager:

```
conda env create -f environment.yml
```

And then activate the environment:

```
conda activate tapioca
```

### Installing

We can install the package through pip by using the `Makefile`:

```
make install
```

## License

This is free software: you can redistribute it and/or modify it under the terms
of the **BSD 3-clause License**. A copy of this license is provided in
[LICENSE](https://github.com/aguspesce/tapioca/blob/master/LICENSE).

