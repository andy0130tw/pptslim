# pptslim

![pptslim logo](https://og-image.now.sh/**PPT**Slim.png?theme=light&md=1&fontSize=150px&images=https%3A%2F%2Fassets.zeit.co%2Fimage%2Fupload%2Ffront%2Fassets%2Fdesign%2Fhyper-color-logo.svg&images=https%3A%2F%2Ffonts.gstatic.com%2Fs%2Fi%2Fmaterialicons%2Fpicture_as_pdf%2Fv4%2F48px.svg&widths=0&widths=400&heights=0&heights=400)

讓你手邊的 PPT 檔* ~~受~~瘦到能被線上服務轉成 PDF。Make your PPTX files slim enough to be converted into PDFs.

\* 只支援 PowerPoint 2007+，也就是 OOXML 格式的簡報檔

# Dependencies

* **pngquant**: 專門用來壓縮 PNG，雖然是 lossy 的但看起來效果還不錯
* **ImageMagick**: 取 GIF 的第一個畫格重新匯出，也用來做 PNG 以外的圖片壓縮
* ~~**ffmpeg** (optional): 把影片換成隨便一個很小的影片檔案，因為看起來縮圖是另外產的~~
