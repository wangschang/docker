import requests
import time
import os,sys
'''
查询本地仓库中上传的版本
并删除对应的版本
1.列出所有镜像和版本 
   修改仓库地址 并运行 python3  register_image.py
2.删除仓库中的某个版本
  python3  register_image.py single 镜像名称 tag 多个tag使用,分隔
'''
class Docker(object):

    def restart(self):
        # 执行arbage-collect命令，删除未被引用的layer
        os.system("docker exec `docker ps | grep registry | awk '{print $1}'` registry garbage-collect /etc/docker/registry/config.yml")
        # 重启registry容器
        os.system("docker restart `docker ps | grep registry | awk '{print $1}'`")

    def get_repos(self,hub):
        get_repos_url = '%s/v2/_catalog' % (hub)
        res = requests.get(get_repos_url).json()
        return res['repositories']

    def __init__(self, hub):
        self.hub = hub

    @staticmethod
    def get_tag_list(hub, repo):
        # 获取这个repo的所有tags
        tag_list_url = '%s/v2/%s/tags/list' % (hub, repo)
        r1 = requests.get(url=tag_list_url)
        tag_list = r1.json().get('tags')
        return tag_list

    def main(self):
        hub = self.hub
        repos = self.get_repos(hub=hub)
        for repo in repos:
            print(repo)
            tag_list = self.get_tag_list(hub=hub, repo=repo)
            if isinstance(tag_list,list) and  len(tag_list) > 0:
                tag_list.sort()
            print('开始处理 %s : %s' % (repo, tag_list))
            #self.delete_images(hub=hub, repo=repo)
        #self.restart()

    def is_valid_date(self,str):
      '''判断是否是一个有效的日期字符串'''
      try:
        time.strptime(str, "%Y%m%d%H%M%S")
        return True
      except:
        return False
        """
        下面删除镜像的处理逻辑，可自定义编写
        我是根据时间戳作为镜像的标签，实现的思路是按照时间排序，保留最新的2个版本
        """
    def delete_images(self, hub, repo):
        tag_list = self.get_tag_list(hub=hub, repo=repo)
        print('开始处理 %s : %s' % (repo, tag_list))
        num = 0
        try:
            # 比如我所有服务的标签有三种：latest、SNAPSHOT、YYYYMMddHHmmss(时间戳)
          del_tag_list = []
          for tag in tag_list:
            # 标签是latest或者含有SNAPSHOT忽略删除
            if tag == 'latest' or 'SNAPSHOT' in tag :
                print('%s 忽略 %s 删除' % (repo, tag))
            elif self.is_valid_date(str=tag):
                print('%s 符合时间戳标签' % (tag))
                del_tag_list.append(tag)
          # 按照时间排序
          del_tag_list.sort()
          # 保存最新2个版本
          for item in del_tag_list[:-2]:
            print('%s 删除 %s' % (repo, item))
            # 获取image digest摘要信息
            get_info_url = '{}/v2/{}/manifests/{}'.format(hub, repo, item)
            header = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
            r2 = requests.get(url=get_info_url, headers=header, timeout=10)
            digest = r2.headers.get('Docker-Content-Digest')

            # 删除镜像
            delete_url = '%s/v2/%s/manifests/%s' % (hub, repo, digest)
            r3 = requests.delete(url=delete_url)
            if r3.status_code == 202:
        except Exception as e:
            print(str(e))

        print('%s 共删除了%i个历史镜像' % (repo, num))
        print('------------------------------------------------------------')
    '''delete special tag '''
    def deletesingle(self,hub,repo,tags):
        taglist = []
        num = 0
        if "," in tags:
            taglist = tags.split(",")
        else:
            taglist.append(tags)
        try:
            for item in taglist:
                print('%s 删除 %s' % (repo, item))
                # 获取image digest摘要信息
                get_info_url = '{}/v2/{}/manifests/{}'.format(hub, repo, item)
                header = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
                r2 = requests.get(url=get_info_url, headers=header, timeout=10)
                digest = r2.headers.get('Docker-Content-Digest')

                # 删除镜像
                delete_url = '%s/v2/%s/manifests/%s' % (hub, repo, digest)
                r3 = requests.delete(url=delete_url)
                if r3.status_code == 202:
                    num += 1
        except Exception as e:
            print(str(e))
        print('%s 共删除了%i个历史镜像' % (repo, num))

if __name__ == '__main__':
    hub = 'http://127.0.0.1:5000'#仓库地址
    d = Docker(hub=hub)
    if len(sys.argv) >1:
        typeid = sys.argv[1]
    else:
        typeid = ""
    if typeid == "":
        d.main()
    elif typeid == "single":
        if len(sys.argv)!=4:
            print("args is 3 at least")
        else:
            repo = sys.argv[2]
            tags = sys.argv[3]
            d.deletesingle(hub=hub,repo=repo,tags=tags)
    else:
        print("params is error")
