export interface TextImportFile {
  file: File;
  relativePath: string;
}

interface FileSystemEntryLike {
  isFile: boolean;
  isDirectory: boolean;
  name: string;
  fullPath?: string;
}

interface FileSystemFileEntryLike extends FileSystemEntryLike {
  file: (success: (file: File) => void, error?: (error: DOMException) => void) => void;
}

interface FileSystemDirectoryEntryLike extends FileSystemEntryLike {
  createReader: () => {
    readEntries: (
      success: (entries: FileSystemEntryLike[]) => void,
      error?: (error: DOMException) => void,
    ) => void;
  };
}

interface DataTransferItemWithEntry {
  webkitGetAsEntry?: () => FileSystemEntryLike | null;
}

const TEXT_EXTENSIONS = new Set([".txt", ".md"]);
const SYSTEM_FILE_NAMES = new Set([".ds_store", "thumbs.db"]);

function extensionOf(path: string): string {
  const match = path.toLowerCase().match(/\.[^.\\/]+$/);
  return match?.[0] ?? "";
}

function isIgnoredPath(path: string): boolean {
  const parts = path.replace(/\\/g, "/").split("/").filter(Boolean);
  return parts.some((part) => {
    const lower = part.toLowerCase();
    return SYSTEM_FILE_NAMES.has(lower) || part.startsWith(".") || part.startsWith("~") || part.startsWith("._");
  });
}

export function isTextImportPath(path: string): boolean {
  return TEXT_EXTENSIONS.has(extensionOf(path)) && !isIgnoredPath(path);
}

export function naturalComparePath(a: string, b: string): number {
  return a.localeCompare(b, "zh-CN", { numeric: true, sensitivity: "base" });
}

function fileFromEntry(entry: FileSystemFileEntryLike): Promise<File> {
  return new Promise((resolve, reject) => {
    entry.file(resolve, reject);
  });
}

function readDirectoryEntries(entry: FileSystemDirectoryEntryLike): Promise<FileSystemEntryLike[]> {
  const reader = entry.createReader();
  const entries: FileSystemEntryLike[] = [];

  return new Promise((resolve, reject) => {
    const readBatch = () => {
      reader.readEntries((batch) => {
        if (batch.length === 0) {
          resolve(entries);
          return;
        }
        entries.push(...batch);
        readBatch();
      }, reject);
    };

    readBatch();
  });
}

async function collectEntry(entry: FileSystemEntryLike, basePath = ""): Promise<TextImportFile[]> {
  const name = entry.name;
  const currentPath = basePath ? `${basePath}/${name}` : name;

  if (entry.isFile) {
    if (!isTextImportPath(currentPath)) return [];
    const file = await fileFromEntry(entry as FileSystemFileEntryLike);
    return [{ file, relativePath: currentPath }];
  }

  if (entry.isDirectory) {
    const children = await readDirectoryEntries(entry as FileSystemDirectoryEntryLike);
    const nested = await Promise.all(children.map((child) => collectEntry(child, currentPath)));
    return nested.flat();
  }

  return [];
}

export async function collectDroppedTextFiles(dataTransfer: DataTransfer): Promise<TextImportFile[]> {
  const itemEntries = Array.from(dataTransfer.items)
    .map((item) => (item as unknown as DataTransferItemWithEntry).webkitGetAsEntry?.())
    .filter((entry): entry is FileSystemEntryLike => Boolean(entry));

  if (itemEntries.length > 0) {
    const collected = await Promise.all(itemEntries.map((entry) => collectEntry(entry)));
    return collected.flat().sort((a, b) => naturalComparePath(a.relativePath, b.relativePath));
  }

  return textFilesFromFileList(dataTransfer.files);
}

export function textFilesFromFileList(files: FileList | File[]): TextImportFile[] {
  return Array.from(files)
    .map((file) => ({
      file,
      relativePath: (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name,
    }))
    .filter((entry) => isTextImportPath(entry.relativePath))
    .sort((a, b) => naturalComparePath(a.relativePath, b.relativePath));
}

export function appendImportFiles(formData: FormData, files: TextImportFile[]): void {
  files.forEach((entry) => {
    formData.append("files", entry.file, entry.file.name);
    formData.append("relative_paths", entry.relativePath);
  });
}
