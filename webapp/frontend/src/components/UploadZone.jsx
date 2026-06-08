import { useState, useRef, useCallback } from 'react'

const ACCEPTED_TYPES = {
  'application/json': true,
  'application/pdf': true,
  'image/jpeg': true,
  'image/png': true,
  'image/webp': true,
}
const ACCEPTED_EXTENSIONS = ['.json', '.pdf', '.jpg', '.jpeg', '.png', '.webp']

function isValidFile(file) {
  if (ACCEPTED_TYPES[file.type]) return true
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  return ACCEPTED_EXTENSIONS.includes(ext)
}

export default function UploadZone({ onUpload }) {
  const [dragOver, setDragOver] = useState(false)
  const [fileError, setFileError] = useState('')
  const inputRef = useRef(null)

  const handleFile = useCallback((file) => {
    setFileError('')
    if (!file) return
    if (!isValidFile(file)) {
      setFileError(`Unsupported file type: "${file.name}". Accepted: PDF, JPG, PNG, JSON`)
      return
    }
    onUpload(file)
  }, [onUpload])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }, [handleFile])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const handleInputChange = useCallback((e) => {
    const file = e.target.files[0]
    handleFile(file)
    // Reset input so same file can be re-uploaded
    e.target.value = ''
  }, [handleFile])

  return (
    <div>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`
          relative rounded-2xl border-2 border-dashed cursor-pointer
          transition-all duration-200 group
          ${dragOver
            ? 'border-indigo-500 bg-indigo-950/30 scale-[1.01]'
            : 'border-slate-700 hover:border-slate-500 bg-slate-900/40 hover:bg-slate-900/60'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleInputChange}
        />
        <div className="flex flex-col items-center justify-center py-14 px-6 text-center">
          <div className={`
            w-16 h-16 rounded-2xl flex items-center justify-center mb-5 transition-colors duration-200
            ${dragOver ? 'bg-indigo-600' : 'bg-slate-800 group-hover:bg-slate-700'}
          `}>
            {dragOver ? (
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
            ) : (
              <svg className="w-8 h-8 text-slate-400 group-hover:text-slate-300 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
          </div>

          <p className="text-lg font-semibold text-white mb-1">
            {dragOver ? 'Release to analyze' : 'Drop your invoice here'}
          </p>
          <p className="text-sm text-slate-400 mb-4">
            or <span className="text-indigo-400 group-hover:text-indigo-300 transition-colors">click to browse</span>
          </p>
          <div className="flex gap-2 flex-wrap justify-center">
            {['PDF', 'JPEG', 'PNG', 'JSON'].map((fmt) => (
              <span key={fmt} className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                {fmt}
              </span>
            ))}
          </div>
        </div>
      </div>

      {fileError && (
        <div className="mt-3 flex items-start gap-2 text-sm text-red-400">
          <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          {fileError}
        </div>
      )}
    </div>
  )
}
