#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "DevoceControl.h"
int main()  
{  
    printf("Hello World!\n");
	
  int iRet = 0;	  
  
  unsigned char enceData[400] = 'happy';
  unsigned long ulEncedData = 0; 
  
  unsigned char OutData[400] = {0};
   unsigned char* result = NULL;

  unsigned long ulOutData = 0; 
  
 unsigned char *pszCert = (unsigned char *)"MIIBkjCCATigAwIBAgIDEX4kMAoGCCqBHM9VAYN1MDkxCzAJBgNVBAYTAkNOMSowKAYDVQQDDCHnp7vliqjkupLogZTnvZHlronlhajmnI3liqHlubPlj7AwHhcNMTQwNzA5MDYzMzQxWhcNMTUwNzA5MDYzMzQxWjA5MQswCQYDVQQGEwJDTjEqMCgGA1UEAwwhMjAxNDAzMjExMTM4MTMwMTIxNjg3QDE1MzIxOTc4Njg1MFkwEwYHKoZIzj0CAQYIKoEcz1UBgi0DQgAETbIYYGiKG3vmWFpaNFc0Aprs6m5pMqxIIJ/OWJav2TbMvcJ5IeqUjmptxD34PCPVnwHmZ0eo1dC92TgLHxRLYKMvMC0wCwYDVR0PBAQDAgbAMBMGA1UdJQQMMAoGCCsGAQUFBwMBMAkGA1UdEwQCMAAwCgYIKoEcz1UBg3UDSAAwRQIgHIGjUmC8hF63PR9SYi2LT3y9AIfEe5oS1X4rKQ/jA5wCIQDrt/gGFlbtkKrwKJBK9r1azSvzY75l7uzptzug1JXUGw==";
  unsigned int uiPszCertLen = strlen((char *)pszCert);
  
  
    
  result= _Z5EncryPhjS_jS_(enceData, ulEncedData, pszCert, uiPszCertLen, 5,OutData);
  
  printf("%s\n",result);
  
  return iRet;
 
}  
