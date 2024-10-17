# Intro

Analyse the ml5.js / Tensorflow code to see what it does under the hood, so we can replicate it in PyTorch.

# Analysis of ml5.js

```
return ml5.neuralNetwork({
    inputs: width * height,
    outputs: ["up", "down", "left", "right", "rotate_cw", "rotate_ccw", "noop"],
    task: "classification",
    neuroEvolution: true,
});
```

7 classes.

See [docs/model.json](docs/model.json) for topology.

# neuroEvolution: true

Builds a static model.

Calls `this.createLayersNoTraining()`

Interpretation:
- adds 0-initialised input sample per classification tag which 
- calls underlying this.neuralNetworkData.addData(xs, ys);
- seems to be some data structure internal to ml5.js used for ???

```
createLayersNoTraining() {
    // Create sample data based on options
    const { inputs, outputs, task } = this.options;

    for (let i = 0; i < outputs.length; i += 1) {
        const inputSample = new Array(inputs).fill(0);
        this.addData(inputSample, [outputs[i]]);
    }

    // TODO: what about inputShape?
    this.neuralNetworkData.createMetadata();
    this.addDefaultLayers();
}
```

# layers

```
// case "classification":
layers = [
    {
        type: "dense",
        units: this.options.hiddenUnits,
        activation: "relu",
    },
    {
        type: "dense",
        activation: "softmax",
    },
];
```

# options

```
DEFAULTS.learningRate = 0.02

loss: "categoricalCrossentropy",
optimizer: tf.train.sgd,
metrics: ["accuracy"],
```

# model

```
tf.sequential()
```

