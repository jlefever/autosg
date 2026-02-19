class Counter {
  constructor(initialValue) {
    this.count = initialValue || 0;
  }

  increment() {
    this.count += 1;
    return this;
  }

  decrement() {
    this.count -= 1;
    return this;
  }

  getValue() {
    return this.count;
  }
}

function createCounter(start) {
  return new Counter(start);
}

const myCounter = createCounter(10);
myCounter.increment().increment().decrement();
console.log(myCounter.getValue());
