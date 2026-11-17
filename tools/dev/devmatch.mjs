#!/usr/bin/env node
// Developer mode: jump straight into a match with chosen fighters and stage,
// skipping the title screen and menus. LOCAL ONLY - never deployed.
//
// How it stays out of players' hands: this file lives in tools/, which is not
// part of the published site (only web/ is). It runs its own local server that
// serves web/ unchanged except for one line of main.js, rewritten in memory to
// pass Ikemen GO's quick-match arguments (-p1 -p2 -s ...) to the engine. The
// deployed main.js never contains any of this.
//
// Usage (repo root):
//   node tools/dev/devmatch.mjs --p1 juanana --p2 grapeman --stage bananaisland
//
// Options:
//   --p1 / --p2 <id>     fighter folder in content/chars (default kfm720)
//   --stage <id>         stage file in content/stages, without .def (default stage0-720)
//   --p1ai / --p2ai <n>  make that side CPU-controlled at level 1-8 (default: P1 you, P2 CPU 4)
//   --human2             P2 is a second human instead of the CPU
//   --rounds <n>         rounds to play before the engine exits (default 2)
//   --time <n>           round time in seconds, -1 for infinite (default 99)
//   --power              start with full, auto-refilling power bars (test supers)
//   --pal1 / --pal2 <n>  palette numbers
//   --headless           no window: run in headless Chrome, take screenshots
//                        into web/test/boot/shots/, print the engine log
//   --duration <s>       headless run length (default 45)
//   --no-build           don't refresh web/content.zip even if content/ changed
//   --port <n>           local port (default 8099)
//   --list               list available fighters and stages, then exit
import http from "node:http";
import fs from "node:fs";
import { promises as fsp } from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const WEB = path.join(ROOT, "web");
const CONTENT = path.join(ROOT, "content");
const ARGV_LINE = 'go.argv = ["ikemen"];';

// ------------------------------------------------------------------ options
function parseArgs(argv) {
	const o = { p1: "kfm720", p2: "kfm720", stage: "stage0-720", rounds: 2, time: 99, port: 8099, duration: 45, p2ai: 4 };
	for (let i = 0; i < argv.length; i++) {
		const a = argv[i];
		const val = () => {
			if (i + 1 >= argv.length) die("missing value for " + a);
			return argv[++i];
		};
		switch (a) {
			case "--p1": o.p1 = val(); break;
			case "--p2": o.p2 = val(); break;
			case "--stage": o.stage = val().replace(/\.def$/, "").replace(/^stages\//, ""); break;
			case "--p1ai": o.p1ai = Number(val()); break;
			case "--p2ai": o.p2ai = Number(val()); break;
			case "--human2": o.p2ai = undefined; break;
			case "--rounds": o.rounds = Number(val()); break;
			case "--time": o.time = Number(val()); break;
			case "--power": o.power = true; break;
			case "--pal1": o.pal1 = Number(val()); break;
			case "--pal2": o.pal2 = Number(val()); break;
			case "--headless": o.headless = true; break;
			case "--duration": o.duration = Number(val()); break;
			case "--no-build": o.noBuild = true; break;
			case "--port": o.port = Number(val()); break;
			case "--list": o.list = true; break;
			case "-h": case "--help": usage(0); break;
			default: die("unknown option " + a);
		}
	}
	return o;
}

function usage(code) {
	const src = fs.readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n");
	console.log(src.filter((l) => l.startsWith("//")).map((l) => l.slice(3)).join("\n"));
	process.exit(code);
}

function die(msg) {
	console.error("devmatch: " + msg);
	process.exit(2);
}

function listFighters() {
	return fs.readdirSync(path.join(CONTENT, "chars")).filter((d) =>
		fs.existsSync(path.join(CONTENT, "chars", d, d + ".def"))).sort();
}

function listStages() {
	return fs.readdirSync(path.join(CONTENT, "stages")).filter((f) => f.endsWith(".def"))
		.map((f) => f.slice(0, -4)).sort();
}

function engineArgs(o) {
	const args = ["ikemen", "-p1", o.p1, "-p2", o.p2, "-s", o.stage, "-rounds", String(o.rounds), "-time", String(o.time)];
	if (o.p1ai) args.push("-p1.ai", String(o.p1ai));
	if (o.p2ai) args.push("-p2.ai", String(o.p2ai));
	if (o.pal1) args.push("-p1.color", String(o.pal1));
	if (o.pal2) args.push("-p2.color", String(o.pal2));
	if (o.power) args.push("-maxpowermode");
	return args;
}

// ------------------------------------------------------------------ content freshness
function newestMtime(dir) {
	let newest = 0;
	for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
		const p = path.join(dir, e.name);
		newest = Math.max(newest, e.isDirectory() ? newestMtime(p) : fs.statSync(p).mtimeMs);
	}
	return newest;
}

function ensureContent(o) {
	const zip = path.join(WEB, "content.zip");
	const wasm = path.join(WEB, "ikemen.wasm");
	if (!fs.existsSync(wasm)) die("web/ikemen.wasm missing - run: bash build/wasm.sh");
	const stale = !fs.existsSync(zip) || newestMtime(CONTENT) > fs.statSync(zip).mtimeMs;
	if (!stale) return;
	if (o.noBuild) {
		console.log("devmatch: warning - content/ changed since web/content.zip was built (--no-build given)");
		return;
	}
	console.log("devmatch: content/ changed, repackaging web/content.zip ...");
	const r = spawnSync("bash", [path.join(ROOT, "build", "wasm.sh"), "--shell-only"], { cwd: ROOT, stdio: "inherit" });
	if (r.status !== 0) die("build/wasm.sh --shell-only failed");
}

// ------------------------------------------------------------------ server
const MIME = {
	".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
	".css": "text/css; charset=utf-8", ".json": "application/json", ".wasm": "application/wasm",
	".zip": "application/zip", ".png": "image/png", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8",
};

function startServer(o, args) {
	const mainSrc = fs.readFileSync(path.join(WEB, "main.js"), "utf8");
	if (!mainSrc.includes(ARGV_LINE)) die("web/main.js no longer contains '" + ARGV_LINE + "' - update devmatch.mjs");
	const devMain = mainSrc.replace(ARGV_LINE,
		"go.argv = " + JSON.stringify(args) + "; console.log('DEVMATCH: ' + go.argv.slice(1).join(' '));");
	const server = http.createServer(async (req, res) => {
		try {
			const u = new URL(req.url, "http://x");
			let rel = decodeURIComponent(u.pathname);
			if (rel.endsWith("/")) rel += "index.html";
			const file = path.normalize(path.join(WEB, rel));
			if (!file.startsWith(WEB + path.sep)) return res.writeHead(403).end();
			const type = MIME[path.extname(file).toLowerCase()] ?? "application/octet-stream";
			const nocache = { "Cache-Control": "no-store" };
			if (rel === "/main.js") {
				return res.writeHead(200, { "Content-Type": type, ...nocache }).end(devMain);
			}
			const size = (await fsp.stat(file)).size;
			const m = req.headers.range ? /^bytes=(\d*)-(\d*)$/.exec(req.headers.range) : null;
			if (m && (m[1] !== "" || m[2] !== "")) {
				let start, end;
				if (m[1] === "") { start = Math.max(0, size - Number(m[2])); end = size - 1; }
				else { start = Number(m[1]); end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1); }
				if (start > end || start >= size) return res.writeHead(416, { "Content-Range": `bytes */${size}` }).end();
				const body = Buffer.alloc(end - start + 1);
				const fh = await fsp.open(file);
				try { await fh.read(body, 0, body.length, start); } finally { await fh.close(); }
				return res.writeHead(206, { "Content-Type": type, "Content-Length": body.length,
					"Content-Range": `bytes ${start}-${end}/${size}`, "Accept-Ranges": "bytes", ...nocache }).end(body);
			}
			const data = await fsp.readFile(file);
			res.writeHead(200, { "Content-Type": type, "Content-Length": data.length, "Accept-Ranges": "bytes", ...nocache });
			res.end(data);
		} catch (e) {
			res.writeHead(404).end("not found");
		}
	});
	return new Promise((resolve, reject) => {
		server.once("error", reject);
		server.listen(o.port, "127.0.0.1", () => resolve(server));
	});
}

// ------------------------------------------------------------------ main
const o = parseArgs(process.argv.slice(2));
const fighters = listFighters();
const stages = listStages();
if (o.list) {
	console.log("fighters: " + fighters.join(", "));
	console.log("stages:   " + stages.join(", "));
	process.exit(0);
}
for (const [side, id] of [["--p1", o.p1], ["--p2", o.p2]]) {
	if (!fighters.includes(id)) die(`${side} ${id}: no such fighter. Available: ${fighters.join(", ")}`);
}
if (!stages.includes(o.stage)) die(`--stage ${o.stage}: no such stage. Available: ${stages.join(", ")}`);

ensureContent(o);
const args = engineArgs(o);
const server = await startServer(o, args).catch((e) => die(`port ${o.port}: ${e.message} (try --port)`));
const url = `http://127.0.0.1:${o.port}/`;
console.log(`devmatch: ${o.p1} vs ${o.p2} on ${o.stage}  ->  engine args: ${args.slice(1).join(" ")}`);

if (o.headless) {
	const chrome = process.env.CHROME_BIN || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
	const child = spawn(process.execPath, ["--experimental-websocket", path.join(WEB, "test", "boot", "run.mjs")], {
		env: { ...process.env, BASE_URL: url.replace(/\/$/, ""), CHROME_BIN: chrome, DURATION: String(o.duration) },
		stdio: ["ignore", "pipe", "inherit"],
	});
	let out = "";
	child.stdout.on("data", (d) => {
		out += d;
		for (const l of String(d).split("\n")) if (/DEVMATCH|Panic|BOOT-ERROR/.test(l)) console.log(l); // live progress
	});
	const kill = () => { try { child.kill("SIGTERM"); } catch (e) { /* gone */ } };
	process.on("SIGINT", () => { kill(); process.exit(130); });
	process.on("SIGTERM", () => { kill(); process.exit(143); });
	const guard = setTimeout(() => { console.log("devmatch: headless run timed out"); kill(); }, (o.duration + 90) * 1000);
	const code = await new Promise((r) => child.on("exit", r));
	clearTimeout(guard);
	const keep = out.split("\n").filter((l) => /DEVMATCH|WARNING|Error|Panic|BOOT-ERROR|OK:|FAIL|screenshot shot/.test(l)
		&& !/GL Driver|Failed to open BGM|Executable not implemented/.test(l));
	console.log([...new Set(keep)].join("\n"));
	console.log("devmatch: screenshots in web/test/boot/shots/");
	server.close();
	process.exit(code ?? 0);
} else {
	spawn("open", [url], { stdio: "ignore", detached: true }).unref();
	console.log(`devmatch: opened ${url}  (Ctrl+C to stop the server)`);
	console.log("devmatch: the engine exits after the match; reload the page to play it again");
}
