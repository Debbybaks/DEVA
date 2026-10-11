import { useEffect, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

/** Illustrative tracers: phase speed v/L, density mapped by Python to |Q|.
 * Schematic world coordinates and radial offsets are not a CFD velocity field. */
export default function FlowParticles({
  a,
  b,
  count,
  velocity,
  length,
  animate,
  speed,
}: {
  a: [number, number, number];
  b: [number, number, number];
  count: number;
  velocity: number;
  length: number;
  animate: boolean;
  speed: number;
}) {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry(),
      position = new Float32Array(count * 3),
      phase = new Float32Array(count),
      radial = new Float32Array(count * 2);
    for (let i = 0; i < count; i++) {
      phase[i] = (i + 0.5) / count;
      const angle = i * 2.399963;
      radial[i * 2] = Math.cos(angle) * 0.045;
      radial[i * 2 + 1] = Math.sin(angle) * 0.045;
    }
    g.setAttribute("position", new THREE.BufferAttribute(position, 3));
    g.setAttribute("phase", new THREE.BufferAttribute(phase, 1));
    g.setAttribute("radial", new THREE.BufferAttribute(radial, 2));
    return g;
  }, [count]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uRate: { value: 0 },
      uA: { value: new THREE.Vector3() },
      uB: { value: new THREE.Vector3() },
    }),
    [],
  );
  useFrame((_, delta) => {
    if (animate) uniforms.uTime.value += Math.min(delta, 0.1) * speed;
    uniforms.uRate.value = velocity / length;
    uniforms.uA.value.set(...a);
    uniforms.uB.value.set(...b);
  });
  return (
    <points geometry={geometry} frustumCulled={false} raycast={() => {}}>
      <shaderMaterial
        uniforms={uniforms}
        transparent
        depthWrite={false}
        vertexShader={`attribute float phase;attribute vec2 radial;uniform float uTime;uniform float uRate;uniform vec3 uA;uniform vec3 uB;void main(){float s=fract(phase+uTime*uRate);vec3 p=mix(uA,uB,s);p.y+=.16+radial.x;p.z+=radial.y;vec4 mv=modelViewMatrix*vec4(p,1.);gl_Position=projectionMatrix*mv;gl_PointSize=clamp(35./max(1.,-mv.z),1.5,3.);}`}
        fragmentShader={`void main(){float r=length(gl_PointCoord-.5);if(r>.5)discard;gl_FragColor=vec4(.67,.88,.84,(1.-smoothstep(.15,.5,r))*.7);}`}
      />
    </points>
  );
}
