#include<iostream>
#include<vector>
#include<algorithm>

using std::vector;
vector<char> sort(vector<char> &myvector)
{
    int N=myvector.size();
    int h=1;
    while(h<N/3) h=3*h+1;  //h=1,4,13...
    while(h>=1)
    {
        for(int i=h;i<N;i++)
        {
            for(int j=i;j>=h && myvector[j]<myvector[j-h];j=j-h)
            {
                auto it=myvector[j];
                myvector[j]=myvector[j-h];
                myvector[j-h]=it;
            }
        }
        h/=3;
    }
    return myvector;


}

int main(int argc,char *argv[])
{
    vector<char> myvector;
    for(int i=1;i<argc;i++)
    {
        myvector.push_back(*(argv[i]));
    }
    myvector=sort(myvector);
    for(int j=0;j<myvector.size();j++)
    {
        std::cout<<myvector[j]<<" ";
    }
}