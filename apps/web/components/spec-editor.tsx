"use client";

import type { PackagingSpec } from "@product-twin/packaging-schema";

type Props = { spec: PackagingSpec; onChange: (next: PackagingSpec) => void };

export function SpecEditor({ spec, onChange }: Props) {
  const setDimension = (key: keyof PackagingSpec["dimensions"], value: number) =>
    onChange({ ...spec, dimensions: { ...spec.dimensions, [key]: value } });

  const numberFields = [
    ["heightMm", "Total height (mm)", 21, 400],
    ["bodyDiameterMm", "Body diameter (mm)", 6, 200],
    ["neckDiameterMm", "Neck diameter (mm)", 4, 80],
    ["capHeightMm", "Cap height (mm)", 6, 120],
  ] as const;

  return (
    <div>
      <p className="eyebrow">Packaging specification</p>
      <h2>Correct the physical model</h2>
      <p className="note">Detected values are a draft. The approved JSON becomes the rendering contract.</p>
      <div className="spec-grid">
        {numberFields.map(([key, label, min, max]) => (
          <div className="field" key={key}>
            <label htmlFor={key}>{label}</label>
            <input
              id={key}
              type="number"
              min={min}
              max={max}
              step="0.1"
              value={spec.dimensions[key]}
              onChange={(event) => setDimension(key, Number(event.target.value))}
            />
          </div>
        ))}
        <div className="field">
          <label htmlFor="shoulder">Shoulder start · {spec.body.shoulderStartRatio.toFixed(2)}</label>
          <input
            id="shoulder"
            type="range"
            min="0.45"
            max="0.95"
            step="0.01"
            value={spec.body.shoulderStartRatio}
            onChange={(event) =>
              onChange({ ...spec, body: { ...spec.body, shoulderStartRatio: Number(event.target.value) } })
            }
          />
        </div>
        <div className="field">
          <label htmlFor="curvature">Shoulder curvature · {spec.body.shoulderCurvature.toFixed(2)}</label>
          <input
            id="curvature"
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={spec.body.shoulderCurvature}
            onChange={(event) =>
              onChange({ ...spec, body: { ...spec.body, shoulderCurvature: Number(event.target.value) } })
            }
          />
        </div>
        <div className="field">
          <label htmlFor="material">Body material</label>
          <select
            id="material"
            value={spec.body.material}
            onChange={(event) =>
              onChange({ ...spec, body: { ...spec.body, material: event.target.value as PackagingSpec["body"]["material"] } })
            }
          >
            <option value="frosted-glass">Frosted glass</option>
            <option value="clear-glass">Clear glass</option>
            <option value="glossy-plastic">Glossy plastic</option>
            <option value="matte-plastic">Matte plastic</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="bodyColor">Body color</label>
          <input
            id="bodyColor"
            type="color"
            value={spec.body.colorHex}
            onChange={(event) => onChange({ ...spec, body: { ...spec.body, colorHex: event.target.value } })}
          />
        </div>
        <div className="field">
          <label htmlFor="closureColor">Closure color</label>
          <input
            id="closureColor"
            type="color"
            value={spec.closure.colorHex}
            onChange={(event) => onChange({ ...spec, closure: { ...spec.closure, colorHex: event.target.value } })}
          />
        </div>
        <div className="field field-inline">
          <label htmlFor="liquidEnabled">Internal liquid</label>
          <input
            id="liquidEnabled"
            type="checkbox"
            checked={spec.liquid.enabled}
            onChange={(event) =>
              onChange({
                ...spec,
                liquid: {
                  ...spec.liquid,
                  enabled: event.target.checked,
                  fillPercent: event.target.checked ? Math.max(spec.liquid.fillPercent, 1) : 0,
                },
              })
            }
          />
        </div>
        <div className="field">
          <label htmlFor="liquidColor">Liquid color</label>
          <input
            id="liquidColor"
            type="color"
            disabled={!spec.liquid.enabled}
            value={spec.liquid.colorHex}
            onChange={(event) => onChange({ ...spec, liquid: { ...spec.liquid, colorHex: event.target.value } })}
          />
        </div>
        <div className="field">
          <label htmlFor="fill">Fill percentage</label>
          <input
            id="fill"
            type="number"
            min="0"
            max="100"
            disabled={!spec.liquid.enabled}
            value={spec.liquid.fillPercent}
            onChange={(event) => onChange({ ...spec, liquid: { ...spec.liquid, fillPercent: Number(event.target.value) } })}
          />
        </div>
        <div className="field">
          <label htmlFor="labelWidth">Label width · {spec.label.widthRatio.toFixed(2)}</label>
          <input
            id="labelWidth"
            type="range"
            min="0.1"
            max="0.95"
            step="0.01"
            value={spec.label.widthRatio}
            onChange={(event) => onChange({ ...spec, label: { ...spec.label, widthRatio: Number(event.target.value) } })}
          />
        </div>
        <div className="field">
          <label htmlFor="labelHeight">Label height · {spec.label.heightRatio.toFixed(2)}</label>
          <input
            id="labelHeight"
            type="range"
            min="0.1"
            max="0.8"
            step="0.01"
            value={spec.label.heightRatio}
            onChange={(event) => onChange({ ...spec, label: { ...spec.label, heightRatio: Number(event.target.value) } })}
          />
        </div>
        <div className="field">
          <label htmlFor="labelVertical">Label vertical position · {spec.label.verticalCenterRatio.toFixed(2)}</label>
          <input
            id="labelVertical"
            type="range"
            min="0.15"
            max="0.85"
            step="0.01"
            value={spec.label.verticalCenterRatio}
            onChange={(event) =>
              onChange({ ...spec, label: { ...spec.label, verticalCenterRatio: Number(event.target.value) } })
            }
          />
        </div>
      </div>
    </div>
  );
}
