from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse
from django.core.files.storage import default_storage
from PIL import Image  
import cv2
import numpy as np 

def resize_image(image, width,height):
    dim = (width, height)
    resize_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resize_image

def jpg2png(img,op):
    # r_channel, g_channel, b_channel = cv2.split(img) 

    img_RGBA = np.insert(
        img,
        3,         #position in the pixel value [ r, g, b, a <-index [3]  ]
        op,         # or 1 if you're going for a float data type as you want the alpha  to be fully white otherwise the entire image will be transparent.
        axis=2,    #this is the depth where you are inserting this alpha channel into
    )
#     print(cv2.split(img))
    return img_RGBA

#在图img的指定位置画点，c代表颜色，op代表透明度
def drawblock(img,x1,y1,c,op):
    height, width, channels = img.shape
    i=0  #op是透明度
    while i<height-1:
        if (i)%4==0:  #每隔4画一次
            if y1<width-1 and x1+i <height-1: #每次画2个点
                img[x1+i,y1]= [c,c,c,op]
                img[x1+i+1,y1]= [c,c,c,op]
        i=i+4   

#在图的指定位置x1,y1画线
def drawcolumn(img,x1,y1,c,op):
    for i in range(4):
        drawblock(img,x1+i,y1+i,c,op)


def mergeto3d(imgl,imgr,distance):
    #合成sbs
    b_channel, g_channel, r_channel,alpha_channel = cv2.split(imgl)
    print('imgl alpha_channel is ',alpha_channel)
    print('imgl ',imgl.shape)
    print('imgr ',imgr.shape)
    combined_img = imgl.copy()
#     distance_factor = 0
#     distance = 24 
    for i in range(len(combined_img)):
        for j in range(len(combined_img[i]) - distance):
            if combined_img[i][j][3]==0:
    #             print ('i,j,combined_img[i][j][3]==0,imgr[i][j + distance][3]',i,j,combined_img[i][j][3],imgr[i][j + distance][3])
    #             print ('------ i,j,combined_img[i][j][0],imgr[i][j + distance][3]',i,j,combined_img[i][j][0],imgr[i][j + distance][0])
    #             print ('------ i,j,combined_img[i][j][1],imgr[i][j + distance][3]',i,j,combined_img[i][j][1],imgr[i][j + distance][1])
    #             print ('------ i,j,combined_img[i][j][2],imgr[i][j + distance][3]',i,j,combined_img[i][j][2],imgr[i][j + distance][2])
                combined_img[i][j][0] = imgr[i][j + distance][0]
                combined_img[i][j][1] = imgr[i][j + distance][1]
                combined_img[i][j][2] = imgr[i][j + distance][2]
                combined_img[i][j][3] = imgr[i][j + distance][3]
    return combined_img

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
@csrf_exempt
def upload(request):
    # filename = 'evil.jpg'
    png2d = '2d.png'
    png3d = '3d.png'
    width2d,height2d = 1954,1080 #放大图片 从size1920*1080 宽度放到1954为最佳3D效果
    #  Saving POST'ed file to storage
    file = request.FILES['image']
    file_name = default_storage.save(file.name, file)

    #  Reading file from storage
    file = default_storage.open(file_name)
    file_url = default_storage.url(file_name)
    # img = cv2.read(file)
    print(cv2.__version__)
    file_name
    print('file_name',file_name)
    print('file',file)
    print('file_url',file_url)
    img = cv2.imread(str(file),cv2.IMREAD_UNCHANGED)
    print('原始 jpg img shape is ',img.shape)

    img = resize_image(img,width2d,height2d)

    height, width, channels = img.shape

    # print(cv2.split(img))

    print('改变尺寸后 jpg img2d shape is ',img.shape)


    #把jpg转换为png ，透明度为250
    if channels==3:
        img_RGBA = jpg2png(img,250)
    else:
        img_RGBA=img.copy()

    print('转换为 png img_RGBA shape is',img_RGBA.shape)

    #图片宽度减半
    newwidth,newheight = int(width/2),height #宽度减半，以便sbs格式

    img = resize_image(img,newwidth,newheight)
    img_RGBA = resize_image(img_RGBA,newwidth,newheight)  


    # b_channel, g_channel, r_channel,alpha_channel = cv2.split(img_RGBA)
    # print('img_RGBA alpha_channel is ',alpha_channel)
    print('宽度减半后 png img_RGBA shape is',img_RGBA.shape)
    # print(png2d)
    # png2d = '2d.png'
    height, width, channels = img_RGBA.shape
    sbsfull = np.zeros((height, width*2, 4), dtype=np.uint8)
    sbsfull.fill(0)

    print('sbsfull shape is X2 width of img_RGBA',sbsfull.shape)

    # img11放sbsfull的·偶数列，img22放sbsfull的奇数列
    sbsfull[:,0::2] = img_RGBA[:,:]
    sbsfull[:,1::2] = img_RGBA[:,:]
    # cv2.imwrite(png2d, img_RGBA)

    sbsleft = sbsfull.copy()
    sbsright = sbsfull.copy()

    #开始在sbsleft和sbsright上画mask，调用drawcolumn函数
    #mask是3d膜片的斜率
    #j是height，i是width
    j= 0-height
    for i in range(0,int(width*2),4):
        j=j+1
        if j>height:
            j=0
        drawcolumn(sbsleft,j,i,255,0) # 白色不透明
        drawcolumn(sbsright,j,i,255,0) # 白色不透明  

    print('sbsright',sbsright.shape)
    print('sbsleft',sbsleft.shape)
    distance=24
    img3d = mergeto3d(sbsleft,sbsright,distance)
    # file_name = default_storage.save('3d'+str(distance)+'.png', img3d)

    print('img3d',img3d.shape)
    cv2.imwrite(file.name,img3d)
    # print('finished'+ '3d'+str(distance)+'.png')

    return HttpResponse("Get Files")
