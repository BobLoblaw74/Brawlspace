// main.js -- boot sequence: mount the content zip(s) into the in-memory fs (lazily
// via its central directory when the host supports Range requests, else in
// full), prefetch the boot-critical prefixes, chdir, then instantiate and
// run ikemen.wasm.
"use strict";

// Captures every stdout/stderr line emitted through fs-shim (see emitLine),
// used by test automation and for surfacing panics.
window.__ikemenBootLog = [];

(() => {
	const overlay = document.getElementById("overlay");
	const bar = document.getElementById("progress-bar");
	const status = document.getElementById("status");
	const errorBox = document.getElementById("error");

	function setStatus(text) { status.textContent = text; }
	function setProgress(frac) { bar.style.width = Math.round(frac * 100) + "%"; }
	function showError(text) {
		overlay.classList.remove("hidden");
		errorBox.style.display = "block";
		errorBox.textContent = text;
		setStatus("Failed to start");
	}

	function fmtMB(n) { return (n / (1024 * 1024)).toFixed(1) + " MB"; }

	async function boot() {
		const dlProgress = (loaded, total) => {
			if (total > 0) {
				setProgress(loaded / total);
				setStatus("Downloading content… " + fmtMB(loaded) + " / " + fmtMB(total));
			} else {
				setStatus("Downloading content… " + fmtMB(loaded));
			}
		};
		// Lazy mode (default): mount only content.zip's central directory and
		// stream file bodies on demand, so chars/stages/sound download when
		// first played. ?eager=1 forces the old full download (debug/escape
		// hatch); hosts without HTTP Range support fall back to it anyway.
		let mode = "eager";
		// Brawlspace: key content.zip by build stamp. Its byte ranges are
		// cached per URL, so after a redeploy a browser could otherwise read
		// the index of one build and file bytes of another ("bad local header
		// ... (changed archive?)"). A fresh URL per build can never mix.
		let stampQuery = "";
		try {
			const vr = await fetch("version.txt", { cache: "no-store" });
			const stamp = vr.ok ? (await vr.text()).trim() : "";
			if (stamp) stampQuery = "?v=" + encodeURIComponent(stamp);
		} catch (e) { /* no stamp (bare static host): plain URLs */ }
		// Brawlspace: the content ships as parts (content-1.zip, ...) listed in
		// content.json, since GitHub Pages rejects files over 100 MiB. The parts
		// never share a path, so each mounts over /ikemen in turn. Without a
		// content.json (an older or hand-made build), fall back to content.zip.
		let contentUrls = ["content.zip" + stampQuery];
		try {
			const pr = await fetch("content.json" + stampQuery, { cache: "no-store" });
			const parts = pr.ok ? (await pr.json()).parts : null;
			if (Array.isArray(parts) && parts.length) contentUrls = parts.map((p) => p + stampQuery);
		} catch (e) { /* no part list: single content.zip */ }
		if (new URLSearchParams(location.search).get("eager") === "1") {
			setStatus("Downloading content…");
			for (const url of contentUrls) await mountZip(url, "/ikemen", dlProgress);
			console.log("fs: eager mode forced (?eager=1)");
		} else {
			setStatus("Fetching content index…");
			let res = null;
			for (const url of contentUrls) {
				const r = await mountZipIndex(url, "/ikemen", { onProgress: dlProgress });
				res = res ? { lazy: res.lazy && r.lazy, files: res.files + r.files } : r;
			}
			if (res.lazy) {
				mode = "lazy";
				console.log("fs: lazy index mounted, " + res.files + " files from " + contentUrls.length + " part(s)");
				// Boot-critical prefixes, prefetched in parallel so boot is
				// not a waterfall of tiny Range requests: data/ and font/
				// (motif, lifebar, fonts), external/ (the engine runs
				// external/script/*.lua at startup), video/ (storyboard
				// videos, if any are added). chars/, stages/ and
				// sound/ (the 5.7 MB soundfont) stay lazy.
				setStatus("Downloading core data…");
				await prefetchLazy("/ikemen", ["data/", "font/", "external/", "video/"], (done, total) => {
					if (total > 0) {
						setProgress(done / total);
						setStatus("Downloading core data… " + fmtMB(done) + " / " + fmtMB(total));
					}
				});
				const st = globalThis.__fsLazyStats;
				console.log("fs: boot prefetch done, " + st.hydrated + "/" + st.files + " files hydrated (" + fmtMB(st.hydratedBytes) + " of " + fmtMB(st.bytes) + ")");
			} else {
				console.log("fs: host lacks Range support, downloaded full bundle");
			}
		}
		setProgress(1);

		// User-supplied game overlay (loader.js): mounts a zip stored in
		// IndexedDB over /ikemen. Catches its own errors; never blocks boot.
		if (window.__ikemenLoader) {
			await window.__ikemenLoader.applyStoredOverlay(setStatus, setProgress);
		}

		globalThis.process.chdir("/ikemen");

		setStatus("Loading engine… (" + (mode === "lazy" ? "streaming content on demand" : "full bundle downloaded") + ")");
		const go = new Go();
		go.argv = ["ikemen"];
		let result;
		try {
			result = await WebAssembly.instantiateStreaming(fetch("ikemen.wasm"), go.importObject);
		} catch (e) {
			// Fallback for servers without application/wasm MIME.
			const resp = await fetch("ikemen.wasm");
			if (!resp.ok) throw new Error("ikemen.wasm: HTTP " + resp.status);
			result = await WebAssembly.instantiate(await resp.arrayBuffer(), go.importObject);
		}

		overlay.classList.add("hidden");
		showControlsHint();
		let exitCode = 0;
		go.exit = (code) => { exitCode = code; };
		await go.run(result.instance); // resolves on normal exit, throws on panic/trap
		const msg = "Engine exited with code " + exitCode;
		window.__ikemenBootLog.push(msg);
		if (exitCode !== 0) showError(msg + "\n\nLast output:\n" + window.__ikemenBootLog.slice(-20).join("\n"));
		else setStatus(msg);
	}

	// Autoplay policy: resume WebAudio on the first user gesture. The Go side
	// (audio_js.go) registers window.__ikemenResumeAudio once audio is up.
	const resumeAudio = () => { if (window.__ikemenResumeAudio) window.__ikemenResumeAudio(); };
	window.addEventListener("pointerdown", resumeAudio);
	window.addEventListener("keydown", resumeAudio);

	// Build stamp (written by build/wasm.sh at package time): shown in the
	// footer; loader.js "Check for updates" compares it against a fresh fetch.
	fetch("version.txt").then((r) => (r.ok ? r.text() : null)).then((t) => {
		if (!t) return;
		window.__ikemenBuild = t.trim();
		const credit = document.getElementById("credit");
		if (credit) credit.append(" · build " + window.__ikemenBuild);
	}).catch(() => { /* stamp is optional (absent on bare static hosts) */ });

	boot().catch((err) => {
		const detail = (err && err.stack) ? err.stack : String(err);
		window.__ikemenBootLog.push("BOOT-ERROR: " + detail);
		console.error(err);
		showError(detail + "\n\nLast output:\n" + window.__ikemenBootLog.slice(-20).join("\n"));
	});
})();

// Transient controls hint shown once the engine takes over; any keypress or
// 10 seconds dismisses it. Suppressed on touch devices (they get the overlay
// gamepad instead).
function showControlsHint() {
	if (window.matchMedia && window.matchMedia("(pointer: coarse)").matches) return;
	const el = document.createElement("div");
	el.textContent = "Enter = confirm/start · Arrows = move · Z X C / A S D = attack · Esc = back · F8 = load game";
	el.style.cssText = "position:fixed;left:50%;bottom:2.2rem;transform:translateX(-50%);" +
		"background:rgba(10,10,14,.85);color:#ddd;padding:.55em 1.1em;border-radius:2em;" +
		"font:14px/1.4 system-ui,sans-serif;z-index:40;pointer-events:none;transition:opacity .6s;white-space:nowrap";
	document.body.appendChild(el);
	const bye = () => {
		el.style.opacity = "0";
		setTimeout(() => el.remove(), 700);
		window.removeEventListener("keydown", bye);
	};
	window.addEventListener("keydown", bye);
	setTimeout(bye, 10000);
}
