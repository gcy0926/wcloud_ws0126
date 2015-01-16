// example.cpp : Defines the entry point for the console application.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "DevoceControl.h"

int main(int argc, char* argv[])
{

  printf("Hello Decode!\n");
	
  int iRet = 0;	  
  
  unsigned char enceData[400] = {0};
  unsigned long ulEncedData = 0; 
  
  unsigned char OutData[400] = {0};
  unsigned long ulOutData = 0; 
  
 unsigned char *pszCert = (unsigned char *)"MIICAjCCAaigAwIBAgIDEYGEMAoGCCqBHM9VAYN1MDkxCzAJBgNVBAYTAkNOMSowKAYDVQQDDCHnp7vliqjkupLogZTnvZHlronlhajmnI3liqHlubPlj7AwHhcNMTQwODEyMDkwMTAyWhcNMTUwODEyMDkwMTAyWjA9MQswCQYDVQQGEwJDTjEuMCwGA1UEAwwlMjAxNDAzMjExMTM4MTMwMTIxNjg3QDg2Mjc2OTAyNTM0NDUzOTBZMBMGByqGSM49AgEGCCqBHM9VAYItA0IABK6KjI3a/duWGrE0Ivwitg/scMb9v9d105swiNB679DbZJZqCY2OMTmVIUf20/RCTuH7qaua8HuNkjxLGEcrRSujgZowgZcwCwYDVR0PBAQDAgbAMB0GA1UdDgQWBBQDEpCWweqh+yfnpHDHPxiKJj7w0jBpBgMqBRUEYgxgTUVVQ0lRQ1owd1NNSFFOUGE3NDJiUkZEQnVUaGxiUWt6Y09xRUx5c2ZWM0IyR3dtSEFJZ1psMDZyMGt6UjB6ZTVSUEcxNWR4amEvYUtObTgwQ3VlRXJFeUxXWUlPVms9MAoGCCqBHM9VAYN1A0gAMEUCIHlFDQOTPtuDc3N5Gas/h48H9xJOzqmBIEsihUF4pvjvAiEA00bpbG1wgf02MLxSRbcz5ts+ko+Hm9wL4Pz5Lqdx7KY=";
  unsigned int uiPszCertLen = strlen((char *)pszCert);
  
  FILE *fp = fopen("./OUTDATA.txt", "rb");
  if(NULL == fp)
  {
    printf("Outdata file notexist1");
  }
  ulEncedData = fread(enceData, 1, 400, fp);
  fclose(fp);

  iRet = InitDeviceControlInterface();
  if(iRet == 0)
  {
     printf("InitDeviceControlInterface successs/n");
  }
  else
  {
     printf("InitDeviceControlInterface error with code:%d" ,iRet );
     return iRet;
  }
  
  
  iRet = instructDecrpRequest(enceData, ulEncedData, pszCert, uiPszCertLen, 5,OutData, (unsigned int *)&ulOutData);
  if(iRet == 0)
  {
     printf("instructDecrpRequest successs, outdata:%s/n", OutData);
  }
  else
  {
     printf("instructDecrpRequest error with code:%d" ,iRet );
     return iRet;
  } 

  iRet = FinalizeDeviceControlInterface();
  if(iRet == 0)
  {
     printf("FinalizeDeviceControlInterface successs/n");
  }
  else
  {
     printf("FinalizeDeviceControlInterface error with code:%d" ,iRet );
     return iRet;
  }

  fp = fopen("./11.txt", "wb");
  if(NULL != fp)
  {
    fwrite(OutData, 1, ulOutData, fp);
  } 
  fclose(fp);
  
  
  return iRet;
}

