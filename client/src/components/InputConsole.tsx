import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { SAMPLES } from "../lib/samples";

interface Props {
  text: string;
  onChange: (t: string) => void;
  onScan: () => void;
  loading: boolean;
  disabled: boolean;
}

const TEXT_EXT = [".txt", ".md", ".log", ".csv", ".json"];
const MAX_FILE_BYTES = 200_000;

export function InputConsole({ text, onChange, onScan, loading, disabled }: Props) {
  const chars = text.length;
  const [dragging, setDragging] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function loadSample(id: string) {
    const s = SAMPLES.find((x) => x.id === id);
    if (s) {
      onChange(s.text);
      setNote(null);
    }
  }

  function readFile(file: File) {
    const name = file.name.toLowerCase();
    if (!TEXT_EXT.some((ext) => name.endsWith(ext))) {
      setNote(`Unsupported in browser: ${file.name}. Text files only (.txt .md .log .csv .json).`);
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setNote("File is too large (limit 200 KB for the demo).");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      onChange(String(reader.result ?? ""));
      setNote(`Loaded ${file.name}`);
    };
    reader.onerror = () => setNote("Could not read that file.");
    reader.readAsText(file);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) readFile(file);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!disabled) onScan();
    }
  }

  return (
    <section className="panel flex h-full flex-col p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="label">Outbound document</span>
        <span className="font-mono text-xs text-muted">{chars.toLocaleString()} chars</span>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        {SAMPLES.map((s) => (
          <button
            key={s.id}
            onClick={() => loadSample(s.id)}
            title={s.hint}
            className="focus-signal rounded-md border border-line bg-ink-700/60 px-2.5 py-1 text-xs text-slate-300 transition hover:border-signal/50 hover:text-signal"
          >
            {s.label}
          </button>
        ))}
        <button
          onClick={() => fileRef.current?.click()}
          title="Load a text file"
          className="focus-signal ml-auto rounded-md border border-dashed border-line px-2.5 py-1 text-xs text-muted transition hover:border-signal/50 hover:text-signal"
        >
          ▲ Upload
        </button>
        <input
          ref={fileRef}
          type="file"
          accept={TEXT_EXT.join(",")}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) readFile(f);
            e.target.value = "";
          }}
        />
      </div>

      <div
        className="relative flex-1"
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <textarea
          value={text}
          onChange={(e) => {
            onChange(e.target.value);
            setNote(null);
          }}
          onKeyDown={onKeyDown}
          placeholder="Paste the text that's about to leave the enclave — or drop a text file here…"
          spellCheck={false}
          className="focus-signal h-full min-h-[240px] w-full resize-none rounded-lg border border-line bg-ink-900/70 p-4 font-mono text-[13px] leading-relaxed text-slate-200 placeholder:text-muted/60"
        />
        {dragging && (
          <div className="pointer-events-none absolute inset-0 grid place-items-center rounded-lg border-2 border-dashed border-signal/70 bg-ink-900/80 font-mono text-sm text-signal">
            Drop to load
          </div>
        )}
      </div>

      {note && <p className="mt-2 font-mono text-[11px] text-signal/80">{note}</p>}

      <div className="mt-4 flex items-center justify-between gap-4">
        <p className="text-xs text-muted">
          Inspected locally. <span className="text-slate-400">Nothing leaves the box.</span>
        </p>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onScan}
          disabled={disabled}
          className="focus-signal group relative inline-flex items-center gap-2 rounded-lg border border-signal/50 bg-signal/10 px-5 py-2.5 font-mono text-sm font-semibold text-signal transition hover:bg-signal/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? (
            <>
              <Spinner /> INSPECTING…
            </>
          ) : (
            <>
              <span className="text-base leading-none">▸</span> INSPECT
              <kbd className="ml-1 hidden rounded border border-signal/30 px-1 text-[10px] text-signal/70 sm:inline">
                ⌘↵
              </kbd>
            </>
          )}
        </motion.button>
      </div>
    </section>
  );
}

function Spinner() {
  return (
    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-signal/30 border-t-signal" />
  );
}
