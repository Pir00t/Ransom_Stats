# About

This project is aimed at providing statistical analysis of ransomware leaks, where a _tree_ file has been provided by the group behind the attack.

From a review of ransomware chats and screenshots from projects such as [ransomch.at](https://ransomch.at) and [ransomlook](https://www.ransomlook.io), the threat groups like to utilise a tree structure when providing evidence of data exfiltration. Unfortunately, they do not always conform to a set _tree_ standard output Therefore, I will update this repo as and when I establish proper parsing for a group.

## NOTE

In order to run the scripts for stats analysis in this repo, you will need to obtain a copy of the _tree_ listing from the ransomware groups leak site. 

Where appropriate for attempting downloads, scripts in this repo require TOR to be installed on your local system. Testing has been conducted on a Linux VM in which the following commands were used for setup:

```bash
sudo apt install tor torsocks
sudo systemctl start tor
sudo systemctl enable tor
netstat -tulpen | grep 9050
curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/ | grep -E 'Congratulations|Sorry|Your IP address appears to be'
```