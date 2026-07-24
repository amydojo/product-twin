import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});

class ResizeObserverStub implements ResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

if (!("ResizeObserver" in globalThis)) {
  Object.defineProperty(globalThis, "ResizeObserver", {
    configurable: true,
    writable: true,
    value: ResizeObserverStub,
  });
}

if (!Blob.prototype.arrayBuffer) {
  Object.defineProperty(Blob.prototype, "arrayBuffer", {
    configurable: true,
    value(this: Blob): Promise<ArrayBuffer> {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.addEventListener("load", () => resolve(reader.result as ArrayBuffer));
        reader.addEventListener("error", () => reject(reader.error));
        reader.readAsArrayBuffer(this);
      });
    },
  });
}
