# Overview
[![Travis](https://travis-ci.org/hunt-genes/layer-slurm.svg?branch=master)](https://travis-ci.org/hunt-genes/layer-slurm) [![license](https://img.shields.io/github/license/hunt-genes/layer-slurm.svg)](./copyright)

This layer provides coordination of munge key setup. The options are:

* act as a provider for a munge pre-shared key supplied from charm config or generated automatically;
* act as a consumer with another charm using this layer doing coordination and providing a munge key.
