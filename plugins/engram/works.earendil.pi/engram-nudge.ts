import { isBashToolResult } from "@earendil-works/pi-coding-agent";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";

function runEngramNudgePlain(input: string, timeoutMs: number): Promise<string> {
  return new Promise((resolve) => {
    const child = spawn("engram", ["nudge", "plain"]);
    let stdout = "";
    let settled = false;

    const finish = (text: string) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(text);
    };

    const timer = setTimeout(() => {
      child.kill();
      finish("");
    }, timeoutMs);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.on("error", () => finish(""));
    child.on("close", () => finish(stdout));

    child.stdin.on("error", () => {
      child.kill();
      finish("");
    });
    child.stdin.write(input);
    child.stdin.end();
  });
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_result", async (event, ctx) => {
    if (!isBashToolResult(event)) return;
    const text = await runEngramNudgePlain(
      JSON.stringify({tool_input: event.input, cwd: ctx.cwd}),
      12_000,
    );
    if (text) {
      return {content: [...event.content, {type: "text", text}]};
    }
  });
}
