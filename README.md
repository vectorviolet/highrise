# 2048 Idle Evolution

Bu projede, Python ile geliştirilmiş bir oyun bulunmaktadır. 2048 Idle Evolution isimli bu oyunda şehrini geliştir ve kazancını katla!

## Başlangıç

### Gereksinimler

Projeyi çalıştırmak için aşağıdaki yazılımlara ihtiyacınız olacaktır:

- Python 3.x
- Gerekli kütüphaneler (aşağıda listelenmiştir)
    - pygame=2.5.2

### Kurulum

Gerekli kütüphaneleri yüklemek için aşağıdaki adımları izleyin:

1. Bu projeyi klonlayın:
    ```sh
    git clone https://github.com/umutcanekinci/2048-idle-evolution.git
    cd 2048-idle-evolution
    ```

2. Sanal ortam oluşturun:
    ```sh
    python -m venv venv
    source venv/bin/activate # Windows kullanıyorsanız: venv\Scripts\activate
    ```

3. Gerekli paketleri yükleyin:
    ```sh
    pip install -r requirements.txt
    ```

### Çalıştırma

Oyunu çalıştırmak için şu komutu kullanın:
```sh
python __main__.py
```

### Kullanım

Oyunun amacı: Şehrini kur ve yönet, şehrin geliri ile daha fazla bina inşa et ve onları birleştirerek şehrini geliştir geliştir ve bu sayede daha fazla kazan.

#### Kontroller: 

##### Binaları hareket ettirme tuşları:

W / Yukarı ok tuşu

A / Sol ok tuşu

S / Aşağı ok tuşu

D / Sağ ok tuşu

Boşluk tuşu → Bina inşa etmek için kullanılır


##### Butonlar ve işlevleri:

INFORMATION MODE butonu → İnceleme modunu açıp kapamayı sağlar.

BUILD butonu → Bina inşa etmeye yarar.

EXPAND butonu → Araziyi genişletmeye yarar.

NEXT AGE butonu → Sonraki çağa geçmeye yarar.

*İnceleme modu aktifken binaların üzerine tıklayıp bilgilerini görebilir, ayrıca onları satabilirsiniz.

### Katkıda Bulunma

Katkıda bulunmak isterseniz, lütfen şu adımları izleyin:

1. Bu depoyu fork'layın (sağ üstteki Fork butonuna tıklayın).

2. Fork'ladığınız depoyu yerel makinenize klonlayın:
```sh
git clone https://github.com/umutcanekinci/2048-idle-evolution.git
cd 2048-idle-evolution
```

3. Yeni bir dal oluşturun (örn: feature/yenilik):
```sh
git checkout -b feature/yenilik
```

4. Değişikliklerinizi yapın ve commit edin:
```sh
git commit -am 'Yeni özellik ekledim'
```

5. Değişikliklerinizi dalınıza iterek GitHub'a gönderin:
```sh
git push origin feature/yenilik
```

6. Pull request oluşturun.

### Lisans

Bu proje MIT Lisansı ile lisanslanmıştır - detaylar için LICENSE dosyasına bakabilirsiniz.

### İletişim

Sorularınız veya önerileriniz için umutcannekinci@gmail.com üzerinden iletişime geçebilirsiniz.
