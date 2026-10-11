import { Component, useEffect, useMemo, useRef } from "react";
import type { ReactNode, RefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import FlowParticles from "./FlowParticles";
import type { OrbitControls as OrbitImpl } from "three-stdlib";
import type { Problem, Candidate, Result, Scenario, Layer } from "./contracts";
import { positions, overview, type Pose } from "./geometry";
export type NetworkProps = {
  problem: Problem;
  candidate: Candidate;
  result: Result;
  scenario: Scenario;
  layer: Layer;
  selection: string | null;
  select: (id: string) => void;
  animate: boolean;
  speed: number;
  pose: Pose;
  setPose: (p: Pose) => void;
  sourceLosses?: string[];
  diagram?: boolean;
  onFrame?: (ms: number) => void;
  hydraulic?: {
    pressure_head_m: Record<string, number | null>;
    diameters_m: number[];
    velocity_ms: number[];
    minimum_pressure_m: number;
    showPressure: boolean;
  };
  twin?: {
    layer:
      | "observations"
      | "residuals"
      | "uncertainty"
      | "hazard"
      | "pressure"
      | "flow";
    measurements: Record<
      string,
      {
        value: number;
        prediction: number;
        residual: number;
        sigma: number;
        unit: string;
        standardized: number;
        parameterRatio: number | null;
      }
    >;
    hazards: Record<string, { probability: number; rate_per_second: number }>;
    gpu: Array<{
      particle_count: number;
      signed_velocity_ms: number;
      length_m: number;
    }>;
  };
  quality?: "standard" | "high";
  // Drei's portal declaration predates nullable React 19 refs; its implementation handles null.
  labelPortal?: RefObject<HTMLElement | null>;
};
const vertex = `uniform float uRadius; varying vec2 vUv; varying vec3 vNormal; void main(){vUv=uv;vNormal=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position+normal*(uRadius-.1),1.0);}`;
const fragment = `uniform float uTime;uniform float uFlux;uniform float uActive;uniform float uUncertainty;uniform vec3 uColor;varying vec2 vUv;varying vec3 vNormal;void main(){float direction=fract(vUv.x*13.0-uTime*uFlux*.85);float tracer=smoothstep(.8,.92,direction)*(1.0-smoothstep(.96,1.0,direction));float lighting=.64+.36*abs(vNormal.z);float hatch=step(.5,fract(vUv.x*34.0+vUv.y*4.0));vec3 ink=uColor*lighting+vec3(.24,.34,.31)*tracer*uActive;float opacity=mix(.9,.42+.3*hatch,uUncertainty);gl_FragColor=vec4(ink,opacity);}`;
function PipeMesh({
  a,
  b,
  index,
  ...props
}: NetworkProps & {
  a: [number, number, number];
  b: [number, number, number];
  index: number;
}) {
  const e = props.problem.edges[index],
    c = props.candidate.capacities[index],
    available = props.scenario.availability[index];
  const flow = props.result.flow[index],
    selected = props.selection === e.id;
  const risk = props.candidate.visual_fields[index];
  const utilization = c * available > 0 ? Math.abs(flow) / (c * available) : 0;
  const color =
    props.layer === "failure" && available < 1
      ? "#d37b6d"
      : props.layer === "capacity"
        ? new THREE.Color("#66b8ac")
            .lerp(new THREE.Color("#d1aa62"), Math.min(1, utilization))
            .getStyle()
        : props.layer === "risk" &&
            risk?.conditional_failure_rate !== null &&
            risk?.conditional_failure_rate !== undefined
          ? new THREE.Color("#66b8ac")
              .lerp(new THREE.Color("#d37b6d"), risk.conditional_failure_rate)
              .getStyle()
          : props.layer === "uncertainty"
            ? "#d1aa62"
            : props.layer === "dependency"
              ? e.corridor.includes("west")
                ? "#96b7c7"
                : "#b8a888"
              : props.layer === "verification"
                ? props.candidate.verification.requirements_pass
                  ? "#66b8ac"
                  : "#d1aa62"
                : "#66b8ac";
  const geometry = useMemo(
    () =>
      new THREE.TubeGeometry(
        new THREE.LineCurve3(new THREE.Vector3(...a), new THREE.Vector3(...b)),
        32,
        0.1,
        10,
        false,
      ),
    [a, b],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  const uniforms = useMemo(
    () => ({
      uRadius: { value: 0.045 + Math.sqrt(c / 100) * 0.065 },
      uTime: { value: 0 },
      uFlux: { value: 0 },
      uActive: { value: 0 },
      uUncertainty: { value: 0 },
      uColor: { value: new THREE.Color("#66b8ac") },
    }),
    [],
  );
  const targetColor = useMemo(
    () => new THREE.Color(selected ? "#f2e5c5" : color),
    [selected, color],
  );
  useFrame((_, delta) => {
    if (props.animate)
      uniforms.uTime.value += Math.min(delta, 0.1) * props.speed;
    uniforms.uRadius.value = THREE.MathUtils.lerp(
      uniforms.uRadius.value,
      props.hydraulic
        ? 0.025 + props.hydraulic.diameters_m[index] * 0.6
        : 0.045 + Math.sqrt(c / 100) * 0.065,
      Math.min(delta * 6, 1),
    );
    uniforms.uFlux.value = props.hydraulic
      ? props.hydraulic.velocity_ms[index]
      : flow / 30;
    uniforms.uActive.value =
      !props.twin &&
      props.layer === "flow" &&
      available > 0 &&
      Math.abs(flow) > 1e-9
        ? 1
        : 0;
    uniforms.uUncertainty.value = THREE.MathUtils.lerp(
      uniforms.uUncertainty.value,
      props.layer === "uncertainty"
        ? risk?.conditional_wilson_95
          ? risk.conditional_wilson_95[1] - risk.conditional_wilson_95[0]
          : 1
        : 0,
      Math.min(delta * 8, 1),
    );
    uniforms.uColor.value.lerp(targetColor, Math.min(delta * 7, 1));
  });
  const middle = a.map((v, i) => (v + b[i]) / 2) as [number, number, number];
  return (
    <group>
      <mesh
        geometry={geometry}
        onClick={(event) => {
          event.stopPropagation();
          props.select(e.id);
        }}
      >
        <shaderMaterial
          vertexShader={vertex}
          fragmentShader={fragment}
          uniforms={uniforms}
          transparent
          depthWrite={false}
        />
      </mesh>
      {props.twin?.layer === "flow" &&
        available > 0 &&
        props.twin.gpu[index]?.particle_count > 0 && (
          <FlowParticles
            a={a}
            b={b}
            count={Math.ceil(
              props.twin.gpu[index].particle_count *
                (props.quality === "high" ? 1 : 0.5),
            )}
            velocity={props.twin.gpu[index].signed_velocity_ms}
            length={props.twin.gpu[index].length_m}
            animate={props.animate}
            speed={props.speed}
          />
        )}
      {props.twin && (
        <TwinMarker
          id={e.id}
          position={[middle[0], 0.65, middle[2]]}
          {...props}
        />
      )}
      {available === 0 && (
        <mesh position={middle} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.2, 0.022, 8, 24]} />
          <meshBasicMaterial color="#d37b6d" />
        </mesh>
      )}
      {(selected || props.layer === "capacity") && (
        <Html
          portal={props.labelPortal as RefObject<HTMLElement> | undefined}
          position={[middle[0], 0.3, middle[2]]}
          center
          className="pipe-label"
        >
          <span>
            {selected ? e.id : ""} {flow.toFixed(1)} /{" "}
            {(c * available).toFixed(1)} m³/h
          </span>
        </Html>
      )}
    </group>
  );
}
function TwinMarker({
  id,
  position,
  ...props
}: NetworkProps & { id: string; position: [number, number, number] }) {
  const data = props.twin?.measurements[id],
    hazard = props.twin?.hazards[id],
    layer = props.twin?.layer;
  if (!props.twin || (!data && !(layer === "hazard" && hazard))) return null;
  if (layer === "flow" || layer === "pressure") return null;
  const risk =
    layer === "hazard"
      ? (hazard?.probability ?? 0)
      : Math.min(1, Math.abs(data?.standardized ?? 0) / 3);
  const color =
    layer === "observations"
      ? "#88b8cc"
      : layer === "uncertainty"
        ? "#d1aa62"
        : new THREE.Color("#66b8ac")
            .lerp(new THREE.Color("#d37b6d"), risk)
            .getStyle();
  return (
    <group position={position}>
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          props.select(id);
        }}
      >
        <ringGeometry args={[0.19, 0.24, 32]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={
            layer === "uncertainty"
              ? Math.min(0.95, 0.25 + (data?.parameterRatio ?? 1) * 0.4)
              : 0.85
          }
          side={THREE.DoubleSide}
        />
      </mesh>
      <Html
        portal={props.labelPortal as RefObject<HTMLElement> | undefined}
        position={[0, 0.27, 0]}
        center
        className="twin-marker"
      >
        <button onClick={() => props.select(id)}>
          {layer === "hazard"
            ? `HAZARD ${((hazard?.probability ?? 0) * 100).toFixed(1)}% / interval`
            : layer === "residuals"
              ? `Δ ${data?.residual.toPrecision(3)} ${data?.unit}`
              : layer === "uncertainty"
                ? `PARAMETER σ / SENSOR σ ${data?.parameterRatio?.toFixed(2) ?? "UNKNOWN"}`
                : `SYNTHETIC ${data?.value.toPrecision(4)} ${data?.unit}`}
        </button>
      </Html>
    </group>
  );
}
function Scene(props: NetworkProps) {
  const p = useMemo(() => positions(props.problem), [props.problem]);
  const controls = useRef<OrbitImpl>(null);
  const { camera } = useThree();
  const transition = useRef<{
    position: THREE.Vector3;
    target: THREE.Vector3;
  } | null>(null);
  useEffect(() => {
    transition.current = {
      position: new THREE.Vector3(...props.pose.position),
      target: new THREE.Vector3(...props.pose.target),
    };
  }, [props.pose]);
  useFrame((_, delta) => {
    props.onFrame?.(delta * 1000);
    const next = transition.current;
    if (next && controls.current) {
      const factor = 1 - Math.exp(-6 * Math.min(delta, 0.1));
      camera.position.lerp(next.position, factor);
      controls.current.target.lerp(next.target, factor);
      controls.current.update();
      if (
        camera.position.distanceToSquared(next.position) < 0.0001 &&
        controls.current.target.distanceToSquared(next.target) < 0.0001
      )
        transition.current = null;
    }
  });
  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[3, 8, 5]} intensity={2} />
      <gridHelper
        args={[22, 44, "#33444a", "#1f2c32"]}
        position={[0, -0.35, 0]}
      />
      {props.problem.edges.map((e, i) => (
        <PipeMesh key={e.id} {...props} a={p[e.tail]} b={p[e.head]} index={i} />
      ))}
      {props.problem.nodes.map((n, i) => {
        const source = (props.problem.supply[n] ?? 0) > 0,
          demand = (props.problem.demand[n] ?? 0) > 0;
        const selected = props.selection === n;
        const lost = props.sourceLosses?.includes(n);
        return (
          <group key={n} position={p[n]}>
            {props.twin && (
              <TwinMarker id={n} position={[0, 1.35, 0]} {...props} />
            )}
            <mesh
              position={[0, 0.2, 0]}
              onClick={(event) => {
                event.stopPropagation();
                props.select(n);
              }}
            >
              {source ? (
                <cylinderGeometry args={[0.33, 0.42, 0.8, 32]} />
              ) : demand ? (
                <boxGeometry args={[0.48, 0.5, 0.48]} />
              ) : (
                <sphereGeometry args={[0.17, 20, 20]} />
              )}
              <meshLambertMaterial
                color={
                  lost
                    ? "#d37b6d"
                    : selected
                      ? "#f2e5c5"
                      : source
                        ? "#7b9baf"
                        : demand
                          ? "#b4b5a1"
                          : "#66b8ac"
                }
              />
            </mesh>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.25, 0]}>
              <ringGeometry args={[0.44, 0.46, 48]} />
              <meshBasicMaterial
                color={selected ? "#f2e5c5" : "#344950"}
                side={THREE.DoubleSide}
              />
            </mesh>
            {props.hydraulic?.showPressure && (
              <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.2, 0]}>
                <circleGeometry args={[0.8, 32]} />
                <shaderMaterial
                  transparent
                  depthWrite={false}
                  uniforms={{
                    uPressure: {
                      value: props.hydraulic.pressure_head_m[n] ?? 0,
                    },
                    uKnown: {
                      value:
                        props.hydraulic.pressure_head_m[n] === null ? 0 : 1,
                    },
                    uThreshold: { value: props.hydraulic.minimum_pressure_m },
                  }}
                  vertexShader="varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}"
                  fragmentShader="uniform float uPressure;uniform float uKnown;uniform float uThreshold;varying vec2 vUv;void main(){float r=length(vUv-.5)*2.;float a=(1.-smoothstep(.35,1.,r))*.6;vec3 c=mix(vec3(.8,.35,.25),vec3(.3,.7,.65),clamp(uPressure/40.,0.,1.));if(uKnown<.5)c=vec3(.4);gl_FragColor=vec4(c,a);}"
                />
              </mesh>
            )}
            <Html
              portal={props.labelPortal as RefObject<HTMLElement> | undefined}
              position={[0, source ? 0.9 : 0.7, 0]}
              center
              className="node-label"
            >
              <button onClick={() => props.select(n)}>
                <b>{n.replaceAll("-", " ")}</b>
                <small>
                  {props.hydraulic?.showPressure
                    ? props.hydraulic.pressure_head_m[n] === null
                      ? "PRESSURE UNKNOWN · ISOLATED"
                      : `${props.hydraulic.pressure_head_m[n].toFixed(2)} m pressure head`
                    : source
                      ? `${props.result.injection[i].toFixed(1)} m³/h supply`
                      : demand
                        ? `${props.result.delivered[i].toFixed(1)} / ${props.result.demand[i].toFixed(1)} m³/h`
                        : "JUNCTION"}
                </small>
              </button>
            </Html>
          </group>
        );
      })}
      <OrbitControls
        ref={controls}
        makeDefault
        onStart={() => {
          transition.current = null;
        }}
        enableDamping
        minDistance={5}
        maxDistance={24}
        maxPolarAngle={Math.PI * 0.47}
        onEnd={() => {
          if (controls.current)
            props.setPose({
              position: camera.position.toArray() as [number, number, number],
              target: controls.current.target.toArray() as [
                number,
                number,
                number,
              ],
            });
        }}
      />
    </>
  );
}
function Diagram(props: NetworkProps) {
  const p = positions(props.problem);
  const point = (name: string) => [
    p[name][0] * 55 + 320,
    p[name][2] * 45 + 190,
  ];
  return (
    <svg
      className="fallback-network"
      viewBox="0 0 640 380"
      role="img"
      aria-label="Analytical network diagram"
    >
      <defs>
        <marker
          id="arrow"
          markerWidth="6"
          markerHeight="6"
          refX="5"
          refY="3"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L6,3 L0,6" fill="#66b8ac" />
        </marker>
      </defs>
      {props.problem.edges.map((e, i) => {
        const a = point(e.tail),
          b = point(e.head);
        return (
          <g key={e.id} onClick={() => props.select(e.id)}>
            <line
              x1={a[0]}
              y1={a[1]}
              x2={b[0]}
              y2={b[1]}
              stroke={
                props.scenario.availability[i] === 0 ? "#d37b6d" : "#66b8ac"
              }
              strokeWidth={2 + Math.sqrt(props.candidate.capacities[i]) * 0.3}
              strokeDasharray={
                props.scenario.availability[i] === 0 ? "6 8" : undefined
              }
              markerStart={props.result.flow[i] < 0 ? "url(#arrow)" : undefined}
              markerEnd={props.result.flow[i] > 0 ? "url(#arrow)" : undefined}
            />
            {props.twin?.measurements[e.id] && (
              <text
                x={(a[0] + b[0]) / 2}
                y={(a[1] + b[1]) / 2 + 18}
                onClick={() => props.select(e.id)}
              >
                SYNTHETIC {props.twin.measurements[e.id].value.toPrecision(3)}{" "}
                {props.twin.measurements[e.id].unit} · Δ{" "}
                {props.twin.measurements[e.id].residual.toPrecision(2)}
              </text>
            )}
            {props.twin?.layer === "hazard" && props.twin.hazards[e.id] && (
              <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2 + 18}>
                HAZARD {(props.twin.hazards[e.id].probability * 100).toFixed(1)}
                % / interval
              </text>
            )}
            <text x={(a[0] + b[0]) / 2} y={(a[1] + b[1]) / 2 - 7}>
              {props.result.flow[i].toFixed(1)} m³/h
            </text>
          </g>
        );
      })}
      {props.problem.nodes.map((n) => {
        const [x, y] = point(n);
        return (
          <g key={n} onClick={() => props.select(n)}>
            <circle
              cx={x}
              cy={y}
              r="12"
              fill={
                props.hydraulic?.showPressure
                  ? props.hydraulic.pressure_head_m[n] === null
                    ? "#66747b"
                    : props.hydraulic.pressure_head_m[n]! <
                        props.hydraulic.minimum_pressure_m
                      ? "#d37b6d"
                      : "#66b8ac"
                  : "#b4b5a1"
              }
            />
            {props.hydraulic?.showPressure && (
              <text x={x} y={y + 28} textAnchor="middle">
                {props.hydraulic.pressure_head_m[n] === null
                  ? "Unknown"
                  : `${props.hydraulic.pressure_head_m[n]!.toFixed(2)} m`}
              </text>
            )}
            {props.twin?.measurements[n] && (
              <text
                x={x}
                y={y + 45}
                textAnchor="middle"
                onClick={() => props.select(n)}
              >
                SYNTHETIC {props.twin.measurements[n].value.toPrecision(3)}{" "}
                {props.twin.measurements[n].unit} · Δ{" "}
                {props.twin.measurements[n].residual.toPrecision(2)}
              </text>
            )}
            <text x={x} y={y - 22} textAnchor="middle">
              {n}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
class CanvasBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
export default function NetworkCanvas(props: NetworkProps) {
  const labelPortal = useRef<HTMLDivElement>(null);
  const available = useMemo(() => {
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl2");
      if (!gl) return false;
      gl.getExtension("WEBGL_lose_context")?.loseContext();
      return true;
    } catch {
      return false;
    }
  }, []);
  if (props.diagram || !available) return <Diagram {...props} />;
  return (
    <CanvasBoundary fallback={<Diagram {...props} />}>
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        <Canvas
          camera={{ position: overview.position, fov: 40 }}
          dpr={props.quality === "high" ? [1, 2] : [0.75, 1.25]}
          gl={{ antialias: true, alpha: false }}
          onCreated={({ gl, setDpr }) => {
            gl.setClearColor("#121b20");
            const context = gl.getContext();
            const info = context.getExtension("WEBGL_debug_renderer_info");
            const renderer = info
              ? String(context.getParameter(info.UNMASKED_RENDERER_WEBGL))
              : "";
            if (/swiftshader|llvmpipe|software/i.test(renderer)) setDpr(0.75);
          }}
        >
          <Scene {...props} labelPortal={labelPortal} />
        </Canvas>
        <div
          ref={labelPortal}
          style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
        />
      </div>
    </CanvasBoundary>
  );
}
