import { useRef, useState } from "react";

interface MediaUploaderProps {
  busy: boolean;
  progress: number;
  onSelect: (file: File) => void;
}

const accept = "audio/*,video/*,.mkv,.flac,.opus";

export function MediaUploader({ busy, progress, onSelect }: MediaUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const choose = (files: FileList | null) => {
    const file = files?.item(0);
    if (file) onSelect(file);
  };

  return (
    <section
      className={`uploader ${dragging ? "is-dragging" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        choose(event.dataTransfer.files);
      }}
      aria-busy={busy}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        hidden
        disabled={busy}
        onChange={(event) => choose(event.target.files)}
      />
      <div className="upload-icon" aria-hidden="true">♪</div>
      <h2>{busy ? "Finding song boundaries…" : "Choose a mix, recording, or video"}</h2>
      <p>
        {busy
          ? `${Math.round(progress * 100)}% complete`
          : "Drop a media file here. Processing stays on this computer."}
      </p>
      {busy ? (
        <progress value={progress} max={1} aria-label="Analysis progress" />
      ) : (
        <button className="primary-button" type="button" onClick={() => inputRef.current?.click()}>
          Select media
        </button>
      )}
    </section>
  );
}
