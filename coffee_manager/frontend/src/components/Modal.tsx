export default function Modal({
  title,
  onClose,
  children,
  maxWidth = 'max-w-2xl',
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
  maxWidth?: string
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div
        className={`bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full ${maxWidth} max-h-[90vh] overflow-y-auto`}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-tremor-border dark:border-dark-tremor-border sticky top-0 bg-white dark:bg-gray-900 z-10">
          <p className="font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            {title}
          </p>
          <button
            onClick={onClose}
            className="text-tremor-content dark:text-dark-tremor-content hover:text-tremor-content-strong dark:hover:text-dark-tremor-content-strong text-xl w-8 h-8 flex items-center justify-center rounded hover:bg-tremor-background-muted dark:hover:bg-dark-tremor-background-muted"
          >
            ×
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}
