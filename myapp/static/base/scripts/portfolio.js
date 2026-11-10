(() => {
    "use strict";

    const root = document.documentElement;
    root.classList.add("js");

    const themeButtons = document.querySelectorAll("[data-theme-toggle]");
    const setTheme = (theme) => {
        root.dataset.theme = theme;
        const nextTheme = theme === "dark" ? "light" : "dark";
        themeButtons.forEach((button) => {
            button.setAttribute("aria-label", `Switch to ${nextTheme} theme`);
            const label = button.querySelector("[data-theme-label]");
            if (label) label.textContent = `${nextTheme === "light" ? "Light" : "Dark"} mode`;
        });
    };

    let theme = root.dataset.theme === "light" ? "light" : "dark";
    try {
        const savedTheme = localStorage.getItem("portfolio-theme");
        if (savedTheme === "light" || savedTheme === "dark") theme = savedTheme;
    } catch (_) {
        // The theme remains usable when browser storage is unavailable.
    }
    setTheme(theme);
    themeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
            setTheme(nextTheme);
            try {
                localStorage.setItem("portfolio-theme", nextTheme);
            } catch (_) {
                // Private browsing and storage policies may prevent persistence.
            }
        });
    });

    const menuToggle = document.querySelector("[data-menu-toggle]");
    const siteNav = document.querySelector("[data-site-nav]");
    if (menuToggle && siteNav) {
        const setMenuOpen = (open) => {
            menuToggle.setAttribute("aria-expanded", String(open));
            menuToggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
            siteNav.classList.toggle("is-open", open);
            menuToggle.classList.toggle("is-open", open);
        };
        setMenuOpen(false);
        menuToggle.addEventListener("click", () => {
            setMenuOpen(menuToggle.getAttribute("aria-expanded") !== "true");
        });
        siteNav.addEventListener("click", (event) => {
            if (event.target.closest("a")) setMenuOpen(false);
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
                setMenuOpen(false);
                menuToggle.focus();
            }
        });
        const desktop = window.matchMedia("(min-width: 1101px)");
        desktop.addEventListener("change", (event) => {
            if (event.matches) setMenuOpen(false);
        });
    }

    const normalizePath = (path) => path.replace(/\/+$/, "") || "/";
    const navigation = [];
    document.querySelectorAll("[data-nav-link]").forEach((link) => {
        try {
            const target = new URL(link.href, window.location.href);
            if (target.origin !== window.location.origin ||
                normalizePath(target.pathname) !== normalizePath(window.location.pathname) ||
                !target.hash) return;
            const section = document.getElementById(decodeURIComponent(target.hash.slice(1)));
            if (section) navigation.push({ link, section });
        } catch (_) {
            // A malformed link must not prevent the remaining controls from working.
        }
    });

    const setCurrentSection = (section) => {
        navigation.forEach(({ link, section: target }) => {
            const current = target === section;
            link.classList.toggle("is-current", current);
            if (current) link.setAttribute("aria-current", "location");
            else link.removeAttribute("aria-current");
        });
    };
    if (navigation.length) {
        const hashSection = navigation.find(({ section }) => `#${section.id}` === window.location.hash);
        setCurrentSection(hashSection ? hashSection.section : document.getElementById("intro"));
        navigation.forEach(({ link, section }) => {
            link.addEventListener("click", () => setCurrentSection(section));
        });
        if ("IntersectionObserver" in window) {
            const visibleSections = new Set();
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) visibleSections.add(entry.target);
                    else visibleSections.delete(entry.target);
                });
                const visible = [...visibleSections].sort((a, b) =>
                    a.getBoundingClientRect().top - b.getBoundingClientRect().top);
                if (visible.length) setCurrentSection(visible[visible.length - 1]);
            }, { rootMargin: "-15% 0px -55% 0px", threshold: 0 });
            const sections = new Set(navigation.map(({ section }) => section));
            const intro = document.getElementById("intro");
            if (intro) sections.add(intro);
            sections.forEach((section) => observer.observe(section));
        }
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const motionButtons = document.querySelectorAll("[data-motion-toggle]");
    const typewriters = [...document.querySelectorAll("[data-typewriter]")].map((element) => {
        const text = element.textContent;
        const index = reducedMotion.matches || root.dataset.motion === "paused" ? text.length : 0;
        element.textContent = text.slice(0, index);
        return { element, text, index, timer: null };
    });
    let motionWasChosen = false;

    const stopTyping = (heading) => window.clearTimeout(heading.timer);
    const scheduleTyping = (heading) => {
        stopTyping(heading);
        if (root.dataset.motion === "paused" || document.hidden || heading.index === heading.text.length) return;
        heading.timer = window.setTimeout(() => {
            heading.index += 1;
            heading.element.textContent = heading.text.slice(0, heading.index);
            scheduleTyping(heading);
        }, 100);
    };
    const setMotion = (paused) => {
        root.dataset.motion = paused ? "paused" : "running";
        motionButtons.forEach((button) => {
            const label = paused ? "Resume motion" : "Pause motion";
            button.setAttribute("aria-label", label);
            const labelElement = button.querySelector("[data-motion-label]");
            if (labelElement) labelElement.textContent = label;
            else button.textContent = label;
        });
        typewriters.forEach(scheduleTyping);
    };
    setMotion(reducedMotion.matches || root.dataset.motion === "paused");
    motionButtons.forEach((button) => {
        button.addEventListener("click", () => {
            motionWasChosen = true;
            setMotion(root.dataset.motion !== "paused");
        });
    });
    reducedMotion.addEventListener("change", (event) => {
        if (!motionWasChosen) setMotion(event.matches);
    });
    const resumeAnimations = () => {
        typewriters.forEach(scheduleTyping);
    };
    document.addEventListener("visibilitychange", resumeAnimations);
    window.addEventListener("pagehide", () => {
        typewriters.forEach(stopTyping);
    });
    window.addEventListener("pageshow", resumeAnimations);

    document.querySelectorAll("[data-project-gallery]").forEach((gallery) => {
        const slides = [...gallery.querySelectorAll("[data-gallery-slide]")];
        const buttons = [...gallery.querySelectorAll("[data-gallery-select]")];
        const controls = gallery.querySelector("[data-gallery-controls]");
        const viewport = gallery.querySelector("[data-gallery-viewport]");
        const playButton = gallery.querySelector("[data-gallery-play]");
        const status = gallery.querySelector("[data-gallery-status]");
        const counter = gallery.querySelector("[data-gallery-current]");
        const count = Math.min(slides.length, buttons.length);
        if (!count) return;
        let current = 0;
        let playing = count > 1 && !reducedMotion.matches && root.dataset.motion !== "paused";
        let hovering = false;
        let inView = !("IntersectionObserver" in window);
        let timer = null;
        const formatCount = (value) => String(value).padStart(2, "0");
        const canPlay = () => playing && inView && !hovering && !document.hidden &&
            !gallery.closest("[hidden]");
        const stopTimer = () => window.clearTimeout(timer);
        const schedule = () => {
            stopTimer();
            if (!canPlay()) return;
            timer = window.setTimeout(() => {
                if (canPlay()) selectScreenshot(current + 1, false, false);
                else schedule();
            }, 5000);
        };
        const setPlaying = (enabled) => {
            playing = count > 1 && enabled;
            if (playButton) playButton.textContent = playing ? "Pause slideshow" : "Play slideshow";
            if (status) status.setAttribute("aria-live", playing ? "off" : "polite");
            schedule();
        };
        const selectScreenshot = (index, focus = false, manual = true) => {
            if (manual) setPlaying(false);
            current = ((index % count) + count) % count;
            slides.forEach((slide, slideIndex) => {
                const selected = slideIndex === current;
                slide.hidden = !selected;
                slide.classList.toggle("is-current", selected);
            });
            buttons.forEach((button, buttonIndex) => {
                button.setAttribute("aria-pressed", String(buttonIndex === current));
            });
            if (counter) counter.textContent = formatCount(current + 1);
            if (status) {
                const caption = slides[current].dataset.galleryCaption;
                status.textContent = `Screenshot ${current + 1} of ${count}${caption ? `: ${caption}` : ""}`;
            }
            if (focus) buttons[current].focus({ preventScroll: true });
            schedule();
        };

        gallery.querySelectorAll("[data-gallery-total]").forEach((total) => {
            total.textContent = formatCount(count);
        });
        buttons.forEach((button, index) => {
            button.addEventListener("click", () => selectScreenshot(index));
            button.addEventListener("keydown", (event) => {
                let target;
                if (event.key === "ArrowRight") target = index + 1;
                else if (event.key === "ArrowLeft") target = index - 1;
                else if (event.key === "Home") target = 0;
                else if (event.key === "End") target = count - 1;
                else return;
                event.preventDefault();
                selectScreenshot(target, true);
            });
        });
        gallery.querySelectorAll("[data-gallery-direction]").forEach((button) => {
            button.addEventListener("click", () => {
                const direction = Number(button.dataset.galleryDirection);
                if (direction === -1 || direction === 1) selectScreenshot(current + direction);
            });
        });
        gallery.addEventListener("focusin", () => setPlaying(false));
        if (playButton) {
            // Remember the pointer action before focusin pauses the slideshow.
            let pointerAction = null;
            playButton.addEventListener("pointerdown", () => { pointerAction = !playing; });
            playButton.addEventListener("pointercancel", () => { pointerAction = null; });
            playButton.addEventListener("keydown", () => { pointerAction = null; });
            playButton.addEventListener("click", () => {
                const next = pointerAction ?? !playing;
                pointerAction = null;
                setPlaying(next);
            });
        }
        gallery.addEventListener("pointerenter", (event) => {
            if (event.pointerType !== "mouse") return;
            hovering = true;
            schedule();
        });
        gallery.addEventListener("pointerleave", (event) => {
            if (event.pointerType !== "mouse") return;
            hovering = false;
            schedule();
        });
        if ("IntersectionObserver" in window) {
            const observer = new IntersectionObserver(([entry]) => {
                inView = entry.isIntersecting && entry.intersectionRatio >= 0.25;
                schedule();
            }, { threshold: [0, 0.25] });
            observer.observe(gallery);
        }
        reducedMotion.addEventListener("change", (event) => {
            if (event.matches) setPlaying(false);
        });
        document.addEventListener("visibilitychange", schedule);
        window.addEventListener("pagehide", stopTimer);
        window.addEventListener("pageshow", schedule);

        if (viewport) {
            let touchStart = null;
            let suppressClick = false;
            let clickTimer = null;
            viewport.addEventListener("pointerdown", (event) => {
                if (event.pointerType !== "touch") return;
                suppressClick = false;
                window.clearTimeout(clickTimer);
                touchStart = event.isPrimary ? { x: event.clientX, y: event.clientY, id: event.pointerId } : null;
            });
            viewport.addEventListener("pointercancel", () => { touchStart = null; });
            viewport.addEventListener("pointerup", (event) => {
                if (!touchStart || event.pointerId !== touchStart.id) return;
                const dx = event.clientX - touchStart.x;
                const dy = event.clientY - touchStart.y;
                touchStart = null;
                if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy) * 1.3) return;
                suppressClick = true;
                clickTimer = window.setTimeout(() => { suppressClick = false; }, 500);
                selectScreenshot(current + (dx < 0 ? 1 : -1));
            });
            viewport.addEventListener("click", (event) => {
                if (!suppressClick) return;
                event.preventDefault();
                event.stopPropagation();
                suppressClick = false;
            }, true);
        }
        gallery.classList.add("is-enhanced-gallery");
        if (controls) controls.hidden = count < 2;
        setPlaying(playing);
        selectScreenshot(0, false, false);
    });

    document.querySelectorAll("[data-project-browser]").forEach((browser) => {
        const tabs = [...browser.querySelectorAll("[data-project-select]")];
        const panels = [...browser.querySelectorAll("[data-project-panel]")];
        const directions = [...browser.querySelectorAll("[data-project-direction]")];
        const count = Math.min(tabs.length, panels.length);
        const formatCount = (value) => String(value).padStart(2, "0");
        let current = 0;

        browser.querySelectorAll("[data-project-total]").forEach((element) => {
            element.textContent = formatCount(count);
        });
        directions.forEach((button) => {
            button.disabled = count < 2;
            button.hidden = count < 2;
        });
        const controls = browser.querySelector("[data-project-controls]");
        if (controls) controls.hidden = count < 2;
        if (!count) {
            browser.querySelectorAll("[data-project-current]").forEach((element) => {
                element.textContent = "00";
            });
            return;
        }

        const selectProject = (index, focus = false) => {
            current = ((index % count) + count) % count;
            tabs.forEach((tab, tabIndex) => {
                const selected = tabIndex === current;
                tab.setAttribute("aria-selected", String(selected));
                tab.tabIndex = selected ? 0 : -1;
                tab.classList.toggle("is-active", selected);
            });
            panels.forEach((panel, panelIndex) => {
                panel.hidden = panelIndex !== current;
                panel.classList.toggle("is-active", panelIndex === current);
            });
            browser.querySelectorAll("[data-project-current]").forEach((element) => {
                element.textContent = formatCount(current + 1);
            });
            const selectedTab = tabs[current];
            if (focus) selectedTab.focus({ preventScroll: true });
            const tablist = selectedTab.closest('[role="tablist"]');
            if (tablist && tablist.scrollWidth > tablist.clientWidth) {
                const rail = tablist.getBoundingClientRect();
                const tab = selectedTab.getBoundingClientRect();
                const leftEdge = rail.left + tablist.clientLeft;
                const rightEdge = leftEdge + tablist.clientWidth;
                if (tab.left < leftEdge) tablist.scrollLeft += tab.left - leftEdge;
                else if (tab.right > rightEdge) tablist.scrollLeft += tab.right - rightEdge;
            }
        };

        tabs.forEach((tab, index) => {
            tab.addEventListener("click", () => selectProject(index));
            tab.addEventListener("keydown", (event) => {
                let target;
                if (event.key === "ArrowRight") target = current + 1;
                else if (event.key === "ArrowLeft") target = current - 1;
                else if (event.key === "Home") target = 0;
                else if (event.key === "End") target = count - 1;
                else return;
                event.preventDefault();
                selectProject(target, true);
            });
        });
        directions.forEach((button) => {
            button.addEventListener("click", () => {
                const direction = Number(button.dataset.projectDirection);
                if (direction === -1 || direction === 1) selectProject(current + direction);
            });
        });
        browser.classList.add("is-enhanced");
        selectProject(0);
    });
})();
