interface FilePickerModalProps {
  open: boolean
  onClose: () => void
  onSelect: (path: string) => void
  initialPath?: string
  title?: string
}

export function FilePickerModal({
  open,
}: FilePickerModalProps) {
  if (!open) return null

  return (
    <div>
      {/* Placeholder for file picker modal */}
    </div>
  )
}
