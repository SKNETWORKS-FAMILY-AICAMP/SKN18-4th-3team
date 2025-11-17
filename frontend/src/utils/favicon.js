// 파비콘을 동그라미로 변환하는 함수
const createCircularFavicon = (imageUrl, size = 32) => {
  return new Promise((resolve) => {
    const img = new Image();
    // 같은 도메인에서 로드하는 경우 crossOrigin 불필요
    img.onload = () => {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext("2d");

        // 동그라미 클리핑 경로 생성
        ctx.beginPath();
        ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();

        // 이미지 그리기 (중앙 정렬)
        const scale = Math.max(size / img.width, size / img.height);
        const scaledWidth = img.width * scale;
        const scaledHeight = img.height * scale;
        const x = (size - scaledWidth) / 2;
        const y = (size - scaledHeight) / 2;

        ctx.drawImage(img, x, y, scaledWidth, scaledHeight);

        // Data URL로 변환
        const dataUrl = canvas.toDataURL("image/png");
        resolve(dataUrl);
      } catch (error) {
        if (process.env.NODE_ENV === "development") {
          console.warn("파비콘 동그라미 변환 실패:", error);
        }
        // 변환 실패 시 원본 URL 반환
        resolve(imageUrl);
      }
    };
    img.onerror = () => {
      // 이미지 로드 실패 시 원본 URL 반환
      resolve(imageUrl);
    };
    img.src = imageUrl;
  });
};

// 파비콘 캐시 무효화: 브라우저가 캐시된 파비콘을 사용하지 않도록 강제로 다시 로드
export const forceReloadFavicon = async () => {
  const version = Date.now(); // 타임스탬프로 매번 다른 값 사용

  // 기존 파비콘 링크 제거
  document.querySelectorAll('link[rel*="icon"]').forEach((link) => {
    link.remove();
  });

  // 새로운 파비콘 링크 동적 추가
  const head = document.getElementsByTagName("head")[0];

  // 동그라미 파비콘 생성 (다양한 크기)
  const faviconSizes = [
    { sizes: "16x16", size: 16, href: "/favicon-16x16.png" },
    { sizes: "32x32", size: 32, href: "/favicon.png" },
    { sizes: "128x128", size: 128, href: "/favicon-128x128.png" },
  ];

  // 동그라미 파비콘 생성 및 추가
  for (const { sizes: sizeAttr, size, href } of faviconSizes) {
    const imageUrl = `${href}?v=${version}`;
    const circularFavicon = await createCircularFavicon(imageUrl, size);

    const link = document.createElement("link");
    link.rel = "icon";
    link.type = "image/png";
    link.sizes = sizeAttr;
    link.href = circularFavicon;
    head.appendChild(link);
  }

  // 기본 파비콘 (32x32 동그라미 버전)
  const defaultImageUrl = `/favicon.png?v=${version}`;
  const defaultCircularFavicon = await createCircularFavicon(
    defaultImageUrl,
    32
  );
  const defaultFavicon = document.createElement("link");
  defaultFavicon.rel = "icon";
  defaultFavicon.type = "image/x-icon";
  defaultFavicon.href = defaultCircularFavicon;
  head.appendChild(defaultFavicon);

  // SVG 파비콘 (동그라미 마스크 적용)
  const svgFavicon = document.createElement("link");
  svgFavicon.rel = "icon";
  svgFavicon.type = "image/svg+xml";
  svgFavicon.href = `/favicon.svg?v=${version}`;
  head.appendChild(svgFavicon);

  // Apple Touch Icon (동그라미 버전)
  const appleImageUrl = `/favicon-128x128.png?v=${version}`;
  const appleCircularFavicon = await createCircularFavicon(appleImageUrl, 128);
  const appleIcon = document.createElement("link");
  appleIcon.rel = "apple-touch-icon";
  appleIcon.href = appleCircularFavicon;
  head.appendChild(appleIcon);

  // Shortcut icon (동그라미 버전)
  const shortcutCircularFavicon = await createCircularFavicon(
    defaultImageUrl,
    32
  );
  const shortcutIcon = document.createElement("link");
  shortcutIcon.rel = "shortcut icon";
  shortcutIcon.href = shortcutCircularFavicon;
  head.appendChild(shortcutIcon);
};
