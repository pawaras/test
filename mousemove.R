mousemove<-function(coord){
  
  library(rMouse)
  library(rJava)
  
  final_cor<-coord
  current_cor<-coord()
  
  p1 <- c(current_cor$x,current_cor$y)
  p2 <- c(final_cor$x,final_cor$y)
  
  
  get_point_between_points<-function(p1, p2, distance,n){
    
    dist_btw_points.x = sqrt((p2[1] - p1[1]) ** 2 + (p2[1] - p1[1]) ** 2)
    dist_btw_points.y = sqrt((p2[2] - p1[2]) ** 2 + (p2[2] - p1[2]) ** 2)
    dist_btw_points<-max(dist_btw_points.x,dist_btw_points.y)
    result<-NULL
    for(i in 1:n){
      
      distance_ratio = distance*i / dist_btw_points
      x = p1[1] + distance_ratio * (p2[1] - p1[1])
      y = p1[2] + distance_ratio * (p2[2] - p1[2])
      temp<-data.frame(x,y)
      
      result<-round(rbind(temp,result),0)
      max=max(p1[1],p2[1])
      min=min(p1[1],p2[1])
      
      result<-result[result$x<max & result$x>min,]
      
    }
    return(result)
  }
  
  
  result<-get_point_between_points(p1,p2,distance = 100,n = 5)
  result<- result[seq(dim(result)[1],1),]
  
  for(i in 1:nrow(result)){
    
    delay(500)
    move(result[i,1],result[i,2])
    
  }
  
  move(final_cor$x,final_cor$y)
  
  
}






