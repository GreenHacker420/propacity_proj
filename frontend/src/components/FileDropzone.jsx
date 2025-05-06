import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { ArrowUpTrayIcon, DocumentTextIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import ProgressBar from './ProgressBar';

const FileDropzone = ({ onFileAccepted, isUploading, uploadProgress = 0 }) => {
  const [file, setFile] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      setFile(selectedFile);
      onFileAccepted(selectedFile);
    }
  }, [onFileAccepted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
    disabled: isUploading
  });

  const clearFile = (e) => {
    e.stopPropagation();
    setFile(null);
  };

  return (
    <div className="w-full">
      <div 
        {...getRootProps()} 
        className={`flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer transition-colors duration-200 ${
          isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
        } ${isUploading ? 'opacity-75 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <div className="flex flex-col items-center justify-center p-5 w-full">
            <p className="mb-3 text-sm text-gray-700 font-medium">Uploading {file.name}</p>
            <div className="w-full max-w-md">
              <ProgressBar progress={uploadProgress} />
            </div>
            <p className="mt-3 text-xs text-gray-500">
              Please wait while we process your file...
            </p>
          </div>
        ) : file ? (
          <motion.div 
            className="flex items-center p-4 bg-primary-100 rounded-lg w-4/5"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <DocumentTextIcon className="w-8 h-8 text-primary-600 mr-3" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-primary-900 truncate">{file.name}</p>
              <p className="text-xs text-primary-700">{(file.size / 1024).toFixed(2)} KB</p>
            </div>
            <button 
              onClick={clearFile} 
              className="p-1 rounded-full hover:bg-primary-200"
            >
              <XMarkIcon className="w-5 h-5 text-primary-700" />
            </button>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <ArrowUpTrayIcon className="w-10 h-10 mb-3 text-gray-400" />
            <p className="mb-2 text-sm text-gray-500">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">CSV files only</p>
            <p className="text-xs text-gray-400 mt-2">
              Must contain 'text' column. Optional: username, timestamp, rating
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileDropzone;
