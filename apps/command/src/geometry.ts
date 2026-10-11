import type { Problem } from "./contracts";
export type Pose = {
  position: [number, number, number];
  target: [number, number, number];
};
export const overview: Pose = { position: [0, 8.5, 12], target: [0, 0, 0] };
export function positions(
  problem: Problem,
): Record<string, [number, number, number]> {
  const groups = [
    problem.nodes.filter((n) => (problem.supply[n] ?? 0) > 0),
    problem.nodes.filter(
      (n) => !(problem.supply[n] > 0) && !(problem.demand[n] > 0),
    ),
    problem.nodes.filter((n) => (problem.demand[n] ?? 0) > 0),
  ];
  return Object.fromEntries(
    groups.flatMap((group, layer) =>
      group.map((name, i) => [
        name,
        [(layer - 1) * 4, 0, (i - (group.length - 1) / 2) * 4],
      ]),
    ),
  );
}
