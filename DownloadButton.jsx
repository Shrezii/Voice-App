import React from 'react';

const DownloadButton = ({ soapNote }) => {
  const downloadTxtFile = () => {
    const element = document.createElement("a");
    const file = new Blob([soapNote], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "soap_note.txt";
    document.body.appendChild(element); // Required for Firefox
    element.click();
    document.body.removeChild(element);
  };

  return (
    <button className="btn download-btn" onClick={downloadTxtFile}>
      📥 Download
    </button>
  );
};

export default DownloadButton;