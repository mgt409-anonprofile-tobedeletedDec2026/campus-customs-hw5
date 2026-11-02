import type { AgentId } from "./types";

export interface Look {
  skin: string;
  hair: string;
  hairStyle: "side" | "bowl" | "short" | "buzz" | "curly" | "silver";
  shirt: string;          // jacket / shirt / cardigan color
  collar: string;
  tie?: string;
  glasses?: boolean;
  beard?: "goatee" | "mustache";
}

export interface Character {
  id: AgentId | "david";
  name: string;
  role: string;
  color: string;      // accent used for their bubbles and badges
  soft: string;       // light background for their bubbles
  ink: string;        // readable text on `soft`
  emoji: string;
  tagline: string;    // shown under their name
  look: Look;
}

// Colors and looks follow each character's on-screen style so they're easy to tell apart.
export const CHARACTERS: Record<AgentId | "david", Character> = {
  boss: {
    id: "boss", name: "Michael Scott", role: "Boss", color: "#2c5ea8", soft: "#e3edfb", ink: "#173a6e",
    emoji: "☕", tagline: "World's Best Boss (self-certified)",
    look: { skin: "#f1c7a5", hair: "#3b2a20", hairStyle: "side", shirt: "#26324f", collar: "#ffffff", tie: "#b03a2e" },
  },
  inventory: {
    id: "inventory", name: "Dwight Schrute", role: "Inventory", color: "#b8860b", soft: "#fff3c4", ink: "#5a4300",
    emoji: "🐻", tagline: "Assistant (to the) Inventory Manager",
    look: { skin: "#f3d2b3", hair: "#6b4523", hairStyle: "bowl", shirt: "#d9a400", collar: "#e9c75a", tie: "#5b3a1a", glasses: true },
  },
  accounting: {
    id: "accounting", name: "Oscar Martinez", role: "Accounting", color: "#1f7a52", soft: "#dcf3e7", ink: "#155238",
    emoji: "🧮", tagline: "Actually, the numbers say no.",
    look: { skin: "#c68f63", hair: "#1d1a17", hairStyle: "short", shirt: "#3f8f6a", collar: "#dfeee6", tie: "#244d3b", beard: "goatee" },
  },
  facilities: {
    id: "facilities", name: "Darryl Philbin", role: "Facilities", color: "#5b45b0", soft: "#e9e4fb", ink: "#3c2f8f",
    emoji: "🔧", tagline: "Warehouse calm, landlord ready",
    look: { skin: "#7a4f37", hair: "#1b1410", hairStyle: "buzz", shirt: "#5d6b86", collar: "#f39c12", beard: "goatee" },
  },
  customer_service: {
    id: "customer_service", name: "Pam Beesly", role: "Customer Service", color: "#c2185b", soft: "#ffe0ef", ink: "#8d1146",
    emoji: "🎨", tagline: "Drafts with a doodle, never sent",
    look: { skin: "#f6d3bd", hair: "#9a4e2a", hairStyle: "curly", shirt: "#ff8cc6", collar: "#ffffff" },
  },
  david: {
    id: "david", name: "David Wallace", role: "Human approver", color: "#1e2a4a", soft: "#eef1f8", ink: "#1e2a4a",
    emoji: "🖊️", tagline: "CFO energy. Signs every check.",
    look: { skin: "#f3cfb0", hair: "#b9bcc2", hairStyle: "silver", shirt: "#3a3f4b", collar: "#ffffff", tie: "#2c5ea8" },
  },
};

export const AGENT_ORDER: AgentId[] = ["boss", "inventory", "accounting", "facilities", "customer_service"];

export function character(id: string | null | undefined): Character | undefined {
  return id ? CHARACTERS[id as AgentId] : undefined;
}
