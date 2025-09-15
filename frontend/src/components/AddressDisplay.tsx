import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { shortenAddress, copyToClipboard } from '../utils/format';

interface AddressDisplayProps {
  address: string;
  shortened?: boolean;
  chars?: number;
  className?: string;
  showCopy?: boolean;
}

export const AddressDisplay: React.FC<AddressDisplayProps> = ({
  address,
  shortened = true,
  chars = 6,
  className = '',
  showCopy = true
}) => {
  const [copied, setCopied] = useState(false);

  const displayAddress = shortened ? shortenAddress(address, chars) : address;

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    const success = await copyToClipboard(address);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!showCopy) {
    return (
      <span className={`font-mono text-sm ${className}`} title={address}>
        {displayAddress}
      </span>
    );
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <span className="font-mono text-sm" title={address}>
        {displayAddress}
      </span>
      <button
        onClick={handleCopy}
        className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200"
        title="Скопировать адрес"
      >
        {copied ? (
          <Check className="w-4 h-4 text-success-600" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>
    </div>
  );
};
