# ทุกงานที่ใช้ GPU gate ด้วยแถว `device` ที่เช็คว่า torch ที่ติดตั้งรันบนการ์ดนี้ได้

แถว `device` ไม่ `ok` เมื่อ compute capability ของการ์ด CUDA ไม่อยู่ใน arch list ของ torch ที่ติดตั้ง และทุกงานที่โหลดโมเดลต้องมีแถวนี้ใน gate ของตัวเอง. Windows NVIDIA ที่รองรับจึงหมายถึงการ์ดที่ build CUDA 12.8 ของ torch รองรับเท่านั้น (GTX 10xx และเก่ากว่าไม่อยู่ใน scope) เพราะเลือกคง CUDA 12.8 แทนการลด CUDA ทั้ง project ให้การ์ดเก่า; ข้อนี้แคบขอบเขต OS ใน ADR-0016. เทียบกับ arch list แทนตัวเลขตายตัว เพื่อให้เกณฑ์ตามเมื่อเปลี่ยน torch.

Source: windows-launch D8, D2; "อยู่ใน arch list" = มี `sm_` major เดียวกับการ์ด ตามกฎของ torch (windows-launch D13)

Links: [PyTorch: Maxwell and Pascal removed in CUDA 12.8 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)

**Status:** accepted
