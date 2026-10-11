import { useReducer } from "react";
import type { Layer } from "./contracts";
export type Mode = "laboratory" | "evolution" | "evidence";
export type UIState = {
  candidate: string | null;
  compare: string | null;
  layer: Layer;
  split: string;
  index: number;
  selection: string | null;
  mode: Mode;
  animate: boolean;
  speed: number;
};
export type Action =
  | { type: "candidate"; id: string }
  | { type: "compare"; id: string | null }
  | { type: "layer"; layer: Layer }
  | { type: "scenario"; index: number }
  | { type: "split"; split: string }
  | { type: "selection"; id: string | null }
  | { type: "mode"; mode: Mode }
  | { type: "animation" }
  | { type: "speed"; speed: number };
export const initial: UIState = {
  candidate: null,
  compare: null,
  layer: "flow",
  split: "heldout",
  index: 0,
  selection: null,
  mode: "laboratory",
  animate: true,
  speed: 1,
};
export function reducer(s: UIState, a: Action): UIState {
  switch (a.type) {
    case "candidate":
      return { ...s, candidate: a.id };
    case "compare":
      return { ...s, compare: a.id };
    case "layer":
      return { ...s, layer: a.layer };
    case "scenario":
      return { ...s, index: a.index };
    case "split":
      return { ...s, split: a.split, index: 0 };
    case "selection":
      return { ...s, selection: a.id };
    case "mode":
      return { ...s, mode: a.mode };
    case "animation":
      return { ...s, animate: !s.animate };
    case "speed":
      return { ...s, speed: a.speed };
  }
}
export function useCommandState() {
  return useReducer(reducer, initial);
}
