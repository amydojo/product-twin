import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { fixtureSpec } from "@/lib/fixture";
import { SpecEditor } from "./spec-editor";

describe("SpecEditor", () => {
  it("exposes the required corrective controls", () => {
    render(<SpecEditor spec={fixtureSpec} onChange={() => undefined} />);
    for (const label of [
      /total height/i,
      /body diameter/i,
      /neck diameter/i,
      /cap height/i,
      /shoulder start/i,
      /shoulder curvature/i,
      /body material/i,
      /body color/i,
      /closure color/i,
      /liquid enabled/i,
      /liquid color/i,
      /fill percentage/i,
      /label width/i,
      /label height/i,
      /label vertical position/i,
    ]) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
  });

  it("emits an updated physical specification", () => {
    const onChange = vi.fn();
    render(<SpecEditor spec={fixtureSpec} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/body diameter/i), { target: { value: "50" } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ dimensions: expect.objectContaining({ bodyDiameterMm: 50 }) }));
  });
});
