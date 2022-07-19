
corr_text<-function(text){

library(tesseract)
library(stringr)
library(rMouse)
library(rJava)
library(magick)
system("nircmd.exe savescreenshot shot.png")
eng <- tesseract("eng")
#OCR_result <- tesseract::ocr_data("shot.png", engine = eng)
OCR_result<-image_read("shot.png")  %>% image_quantize(colorspace = 'gray') %>% ocr_data()
object_box<-OCR_result[!is.na(str_locate(OCR_result$word, text)),]
object_box<-strsplit(object_box$bbox[1],NULL,split = ",")[[1]]
corr<-NULL
corr$x<-round(mean(as.integer(object_box[c(1,3)])))
corr$y<-round(mean(as.integer(object_box[c(2,4)])))
corr
return(corr)
}



  

